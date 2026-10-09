"""Leave-one-interior-thickness-out validation of OpenMC flux surrogates.

Run from the repository root:
    conda activate ml-env
    python ml_surrogate/cross_validate.py

Input:
    ml_surrogate/data/openmc_attenuation_data.csv

Outputs (under ml_surrogate/):
    cross_validation_summary.csv
    cross_validation_predictions.csv
    cross_validation_errors.png
    cross_validation_random_forest_errors.png

This assesses interpolation within 0-30 cm, not extrapolation. The 0 cm
and 30 cm endpoints are always included in the training set. Each other
thickness is omitted in turn, then predicted by a newly fitted model.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_PATH = SCRIPT_DIR / "data" / "openmc_attenuation_data.csv"
MAX_THICKNESS_CM = 30.0


def load_data(path: Path) -> pd.DataFrame:
    """Load and check positive OpenMC tally results for concrete shielding."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing {path}. Copy attenuation_results.csv to this location."
        )

    data = pd.read_csv(path)
    required = {"material", "thickness_cm", "flux", "uncertainty"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing columns in {path}: {sorted(missing)}")

    # Retain the full source CSV; filter only in memory.
    data = data.loc[
        data["material"].astype(str).str.strip().str.lower().eq("concrete")
        & data["thickness_cm"].between(0, MAX_THICKNESS_CM)
    ].copy()

    for field in ("thickness_cm", "flux", "uncertainty"):
        data[field] = pd.to_numeric(data[field], errors="coerce")

    valid = (
        np.isfinite(data["thickness_cm"])
        & np.isfinite(data["flux"])
        & (data["flux"] > 0)
        & np.isfinite(data["uncertainty"])
        & (data["uncertainty"] >= 0)
    )
    if not valid.all():
        raise ValueError("Invalid, zero or non-finite flux/uncertainty in 0-30 cm dataset")

    data = data.sort_values("thickness_cm").reset_index(drop=True)
    if data["thickness_cm"].duplicated().any():
        raise ValueError("Duplicate thickness values in selected dataset")
    if len(data) < 5:
        raise ValueError("Need at least five positive-flux points for validation")
    if not np.isclose(data["thickness_cm"].iloc[0], 0.0):
        raise ValueError("A 0 cm reference point is required")
    if not np.isclose(data["thickness_cm"].iloc[-1], MAX_THICKNESS_CM):
        raise ValueError("A 30 cm endpoint is required")

    return data


def model_templates() -> dict:
    """Same model families and hyperparameters as compare_models.py."""
    return {
        "Log-linear Regression": LinearRegression(),
        "Polynomial Regression (degree 3)": make_pipeline(
            PolynomialFeatures(degree=3, include_bias=False),
            LinearRegression(),
        ),
        "Random Forest": RandomForestRegressor(
            n_estimators=100,
            min_samples_leaf=3,
            random_state=42,
        ),
    }


def validate(data: pd.DataFrame) -> pd.DataFrame:
    """One fit per omitted interior thickness, with no held-out data in training."""
    thickness = data["thickness_cm"].to_numpy(dtype=float)
    observed_flux = data["flux"].to_numpy(dtype=float)
    std_dev = data["uncertainty"].to_numpy(dtype=float)
    log_flux = np.log10(observed_flux)

    # Keep both endpoints in training for every fold (interpolation).
    interior_indices = range(1, len(data) - 1)
    rows = []
    for test_idx in interior_indices:
        train_mask = np.ones(len(data), dtype=bool)
        train_mask[test_idx] = False

        # Always instantiate a fresh model; no information leaks across folds.
        for name, template in model_templates().items():
            model = clone(template)
            model.fit(thickness[train_mask].reshape(-1, 1), log_flux[train_mask])
            predicted_log = float(model.predict(thickness[[test_idx]].reshape(-1, 1))[0])
            predicted_flux = float(10.0 ** predicted_log)
            actual_flux = float(observed_flux[test_idx])

            rows.append({
                "model": name,
                "thickness_cm": float(thickness[test_idx]),
                "openmc_flux": actual_flux,
                "openmc_std_dev": float(std_dev[test_idx]),
                "openmc_relative_uncertainty_pct": float(
                    100.0 * std_dev[test_idx] / actual_flux
                ),
                "predicted_flux": predicted_flux,
                "signed_error_pct": 100.0 * (predicted_flux / actual_flux - 1.0),
                "absolute_log10_error_dex": abs(predicted_log - log_flux[test_idx]),
            })

    return pd.DataFrame.from_records(rows)


def summarise(predictions: pd.DataFrame) -> pd.DataFrame:
    """Report pooled held-out errors; each observation was predicted unseen."""
    rows = []
    for name, group in predictions.groupby("model", sort=False):
        actual = group["openmc_flux"].to_numpy()
        predicted = group["predicted_flux"].to_numpy()
        abs_pct_error = group["signed_error_pct"].abs().to_numpy()

        rows.append({
            "Model": name,
            "Held-out thicknesses": len(group),
            "LOIO log10 MAE (dex)": mean_absolute_error(
                np.log10(actual), np.log10(predicted)
            ),
            "LOIO flux MAPE (%)": np.mean(abs_pct_error),
            "LOIO flux median APE (%)": np.median(abs_pct_error),
            "LOIO flux R2": r2_score(actual, predicted),
        })

    return pd.DataFrame(rows)


def plot_errors(predictions: pd.DataFrame) -> None:
    """Plot signed CV errors alongside indicative OpenMC tally uncertainty."""
    readable_models = ["Log-linear Regression", "Polynomial Regression (degree 3)"]
    names_and_files = [
        (readable_models, "cross_validation_errors.png", "Regression Surrogates"),
        (["Random Forest"], "cross_validation_random_forest_errors.png", "Random Forest"),
    ]

    for selected_models, filename, title in names_and_files:
        fig, ax = plt.subplots(figsize=(9, 5.5))

        # Uncertainty shown as an indicative band about zero, not a surrogate
        # confidence interval. It is the OpenMC tally's relative 1-sigma error.
        one_model = predictions.loc[
            predictions["model"] == "Log-linear Regression"
        ].sort_values("thickness_cm")
        x = one_model["thickness_cm"].to_numpy()
        sigma_pct = one_model["openmc_relative_uncertainty_pct"].to_numpy()
        ax.fill_between(
            x, -sigma_pct, sigma_pct, color="grey", alpha=0.16,
            label="OpenMC relative uncertainty (±1σ; indicative)",
        )

        for name in selected_models:
            group = predictions.loc[predictions["model"] == name].sort_values(
                "thickness_cm"
            )
            ax.plot(
                group["thickness_cm"], group["signed_error_pct"],
                marker="o", markersize=4, label=name,
            )

        ax.axhline(0.0, color="black", linewidth=1)
        ax.set_xlabel("Omitted concrete shielding thickness (cm)")
        ax.set_ylabel("Prediction error relative to OpenMC (%)")
        ax.set_title(f"Leave-One-Interior-Out Prediction Errors: {title}")
        ax.grid(alpha=0.25)
        ax.legend(fontsize=9)
        fig.tight_layout()
        fig.savefig(SCRIPT_DIR / filename, dpi=300)
        plt.close(fig)


def main() -> None:
    data = load_data(DATA_PATH)
    predictions = validate(data)
    summary = summarise(predictions)

    predictions.to_csv(SCRIPT_DIR / "cross_validation_predictions.csv", index=False)
    summary.to_csv(SCRIPT_DIR / "cross_validation_summary.csv", index=False)
    plot_errors(predictions)

    print(
        f"Loaded {len(data)} concrete OpenMC results from 0 to 30 cm; "
        f"withheld each of {len(data) - 2} interior points in turn."
    )
    print("Endpoints (0 and 30 cm) remain in every training set.\n")
    print(summary.to_string(index=False, float_format=lambda value: f"{value:.4g}"))
    print("\nSaved cross-validation summary, predictions and two error plots to ml_surrogate/.")
    print("Results assess interpolation only; OpenMC tallies have statistical error.")


if __name__ == "__main__":
    main()
