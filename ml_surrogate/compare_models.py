"""Compare regression surrogates against OpenMC concrete shielding results.

Run from the repository root:
    conda activate ml-env
    python ml_surrogate/compare_models.py

Input:
    ml_surrogate/data/openmc_attenuation_data.csv
Outputs (all written to ml_surrogate/):
    model_comparison.csv
    test_predictions.csv
    model_comparison.png
    prediction_error.png
    random_forest_error.png
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import PolynomialFeatures


# --------------------------------------------------
# 1. LOAD REAL OPENMC RESULTS
# --------------------------------------------------

script_dir = Path(__file__).resolve().parent
data_file = script_dir / "data" / "openmc_attenuation_data.csv"

if not data_file.is_file():
    raise FileNotFoundError(
        f"Cannot find {data_file}\n"
        "From the repository root, run:\n"
        "  mkdir -p ml_surrogate/data\n"
        "  cp attenuation_results.csv ml_surrogate/data/openmc_attenuation_data.csv"
    )

data = pd.read_csv(data_file)
required_columns = {"material", "thickness_cm", "flux", "uncertainty"}
missing = required_columns - set(data.columns)
if missing:
    raise ValueError(f"Missing required CSV columns: {sorted(missing)}")

# Focus on 0-30 cm, where the OpenMC estimates have better precision.
# The original 0-50 cm data file is left unchanged.
data = data.loc[
    data["material"].str.strip().str.lower().eq("concrete")
    & data["thickness_cm"].between(0, 30)
].copy()

data = data.loc[
    np.isfinite(data["flux"])
    & (data["flux"] > 0)
    & np.isfinite(data["uncertainty"])
    & (data["uncertainty"] >= 0)
    & np.isfinite(data["thickness_cm"])
].sort_values("thickness_cm").reset_index(drop=True)

if data["thickness_cm"].duplicated().any():
    raise ValueError("Duplicate concrete thickness values in the input CSV.")

# We are using a deliberate *interpolation* test. Four well-separated,
# intermediate thicknesses are withheld; 0 and 30 cm remain in training.
# All listed thicknesses must exist in the dataset.
test_thicknesses = [6.0, 14.0, 22.0, 28.0]
required_thicknesses = [0.0, 30.0] + test_thicknesses
for thickness in required_thicknesses:
    if not np.isclose(data["thickness_cm"].to_numpy(), thickness).any():
        raise ValueError(
            f"Expected a result at {thickness:g} cm. "
            "Check that you generated the 0-30 cm data in 2 cm steps."
        )

if len(data) < 10:
    raise ValueError("Too few usable OpenMC results for this comparison.")

data["relative_uncertainty_pct"] = 100.0 * data["uncertainty"] / data["flux"]
print(f"Loaded {len(data)} real OpenMC results between 0 and 30 cm.")
print(
    "Largest relative statistical uncertainty in this subset: "
    f"{data['relative_uncertainty_pct'].max():.1f}%"
)

# The target is log10(flux). Inverse-transform using 10**prediction.
X = data[["thickness_cm"]]
y_log = np.log10(data["flux"])


# --------------------------------------------------
# 2. TRAIN/TEST SPLIT: INTERPOLATION, NOT EXTRAPOLATION
# --------------------------------------------------

is_test = np.isclose(
    data["thickness_cm"].to_numpy()[:, None],
    np.array(test_thicknesses)[None, :],
).any(axis=1)

X_train = X.loc[~is_test]
X_test = X.loc[is_test]
y_train = y_log.loc[~is_test]
y_test = y_log.loc[is_test]

print(f"Training points: {len(X_train)}")
print(f"Held-out test thicknesses (cm): {X_test['thickness_cm'].tolist()}")
print("Endpoints 0 and 30 cm are included in the training set.\n")


# --------------------------------------------------
# 3. DEFINE MODELS
# --------------------------------------------------

models = {
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


# --------------------------------------------------
# 4. TRAIN, EVALUATE AND SAVE TEST PREDICTIONS
# --------------------------------------------------

results = []
actual_flux = data.loc[is_test, "flux"].to_numpy()

# Each row records an *unseen test thickness* and an associated model estimate.
test_predictions = data.loc[
    is_test, ["thickness_cm", "flux", "uncertainty", "relative_uncertainty_pct"]
].copy()
test_predictions = test_predictions.rename(columns={"flux": "openmc_flux"})

for name, model in models.items():
    model.fit(X_train, y_train)

    predicted_log = model.predict(X_test)
    predicted_flux = np.power(10.0, predicted_log)
    percentage_error = 100.0 * (predicted_flux - actual_flux) / actual_flux

    log_mae = mean_absolute_error(y_test, predicted_log)
    flux_mse = mean_squared_error(actual_flux, predicted_flux)
    flux_r2 = r2_score(actual_flux, predicted_flux)
    flux_mape = np.mean(np.abs(percentage_error))

    results.append({
        "Model": name,
        "Test Log10 MAE (dex)": log_mae,
        "Test Flux MSE": flux_mse,
        "Test Flux R2": flux_r2,
        "Test Flux MAPE (%)": flux_mape,
    })

    test_predictions[f"{name} predicted_flux"] = predicted_flux
    test_predictions[f"{name} error_pct"] = percentage_error

    print(name)
    print(f"  Test log10 MAE:  {log_mae:.4f} dex")
    print(f"  Test flux MSE:   {flux_mse:.6g}")
    print(f"  Test flux R2:    {flux_r2:.4f}")
    print(f"  Test flux MAPE:  {flux_mape:.1f}%")
    print()

pd.DataFrame(results).to_csv(script_dir / "model_comparison.csv", index=False)
test_predictions.to_csv(script_dir / "test_predictions.csv", index=False)


# --------------------------------------------------
# 5. FLUX COMPARISON PLOT
# --------------------------------------------------

thickness_range = pd.DataFrame({
    "thickness_cm": np.linspace(0, 30, 301)
})

plt.figure(figsize=(9, 6))

# OpenMC error bars are one standard deviation of the Monte Carlo tally.
for mask, label, marker in [
    (~is_test, "OpenMC training data", "o"),
    (is_test, "OpenMC test data", "s"),
]:
    plt.errorbar(
        data.loc[mask, "thickness_cm"],
        data.loc[mask, "flux"],
        yerr=data.loc[mask, "uncertainty"],
        fmt=marker,
        linestyle="none",
        markersize=4,
        capsize=2,
        label=label,
    )

for name, model in models.items():
    curve_flux = np.power(10.0, model.predict(thickness_range))
    plt.plot(thickness_range["thickness_cm"], curve_flux, label=name)

plt.yscale("log")
plt.xlabel("Concrete shielding thickness (cm)")
plt.ylabel("OpenMC detector flux tally (per source particle)")
plt.title("ML Surrogate Comparison Against OpenMC Results")
plt.xlim(0, 30)
plt.legend()
plt.grid(alpha=0.3, which="both")
plt.tight_layout()
plt.savefig(script_dir / "model_comparison.png", dpi=300)
plt.close()


# --------------------------------------------------
# 6. PREDICTION ERROR PLOT (HELD-OUT DATA ONLY)
# --------------------------------------------------

# Signed relative error = 100 * (surrogate - OpenMC) / OpenMC.
# Positive means the surrogate overpredicts; negative means underpredicts.
# Separate figures keep very large random forest errors from hiding the
# differences between log-linear and polynomial regression.

x_test = X_test["thickness_cm"].to_numpy()

plt.figure(figsize=(9, 5))
for name in ["Log-linear Regression", "Polynomial Regression (degree 3)"]:
    plt.plot(
        x_test,
        test_predictions[f"{name} error_pct"],
        marker="o",
        label=name,
    )

plt.axhline(0, color="black", linewidth=1)
plt.axhline(10, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
plt.axhline(-10, color="gray", linestyle="--", linewidth=0.8, alpha=0.6)
plt.xlabel("Held-out concrete thickness (cm)")
plt.ylabel("Prediction error relative to OpenMC (%)")
plt.title("Test Prediction Errors: Regression Models")
plt.xticks(test_thicknesses)
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(script_dir / "prediction_error.png", dpi=300)
plt.close()

plt.figure(figsize=(9, 5))
plt.plot(
    x_test,
    test_predictions["Random Forest error_pct"],
    marker="o",
    label="Random Forest",
)
plt.axhline(0, color="black", linewidth=1)
plt.xlabel("Held-out concrete thickness (cm)")
plt.ylabel("Prediction error relative to OpenMC (%)")
plt.title("Test Prediction Errors: Random Forest")
plt.xticks(test_thicknesses)
plt.grid(alpha=0.3)
plt.legend()
plt.tight_layout()
plt.savefig(script_dir / "random_forest_error.png", dpi=300)
plt.close()

print("Saved results in ml_surrogate/:")
print("  model_comparison.csv")
print("  test_predictions.csv")
print("  model_comparison.png")
print("  prediction_error.png")
print("  random_forest_error.png")
print("\nNote: These test results assess interpolation at only four thicknesses.")
print("Model rankings may change with a different split or additional data.")
