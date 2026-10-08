
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# --------------------------------------------------
# 1. LOAD DATA
# --------------------------------------------------

data = pd.read_csv("synthetic_data.csv")

# X = input features (shield thickness)
# y = target variable (detector flux)

X = data[["thickness_cm"]]
y = data["detector_flux"]

# --------------------------------------------------
# 2. SPLIT DATA
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# --------------------------------------------------
# 3. DEFINE MODELS
# --------------------------------------------------

models = {
    "Linear Regression": LinearRegression(),

    "Polynomial Regression": make_pipeline(
        PolynomialFeatures(degree=3, include_bias=False),
        LinearRegression()
    ),

    "Random Forest": RandomForestRegressor(
        n_estimators=100,
        min_samples_leaf=3,
        random_state=42
    )
}

# --------------------------------------------------
# 4. TRAIN AND EVALUATE
# --------------------------------------------------

results = []

for name, model in models.items():

    # Train on training data only
    model.fit(X_train, y_train)

    # Predict unseen test data
    predictions = model.predict(X_test)

    # Calculate performance metrics
    mse = mean_squared_error(y_test, predictions)
    r2 = r2_score(y_test, predictions)

    results.append({
        "Model": name,
        "Test MSE": mse,
        "Test R2": r2
    })

    print(f"{name}")
    print(f"  Test MSE: {mse:.6f}")
    print(f"  Test R2:  {r2:.4f}")
    print()

# --------------------------------------------------
# 5. SAVE RESULTS
# --------------------------------------------------

results_df = pd.DataFrame(results)
results_df.to_csv("model_comparison.csv", index=False)

# --------------------------------------------------
# 6. PLOT MODEL PREDICTIONS
# --------------------------------------------------

thickness_range = pd.DataFrame({
    "thickness_cm": np.linspace(0, 50, 200)
})

plt.figure(figsize=(9, 6))

# Plot training and testing data
plt.scatter(
    X_train["thickness_cm"],
    y_train,
    s=18,
    alpha=0.4,
    label="Training data"
)

plt.scatter(
    X_test["thickness_cm"],
    y_test,
    s=25,
    label="Test data"
)

# Plot predictions from each model
for name, model in models.items():

    predictions = model.predict(thickness_range)

    plt.plot(
        thickness_range["thickness_cm"],
        predictions,
        label=name
    )

plt.xlabel("Concrete thickness (cm)")
plt.ylabel("Detector flux (arbitrary units)")
plt.title("Comparison of Regression Models")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig("model_comparison.png", dpi=300)
plt.close()

print("Model comparison completed.")
