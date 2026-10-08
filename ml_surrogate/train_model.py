
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 1. Load the synthetic shielding dataset
data = pd.read_csv("synthetic_data.csv")

x = data["thickness_cm"].to_numpy()
y = data["detector_flux"].to_numpy()

# 2. Split the data into training and testing sets
rng = np.random.default_rng(42)
indices = rng.permutation(len(x))

split = int(0.8 * len(x))
train_indices = indices[:split]
test_indices = indices[split:]

x_train = x[train_indices]
y_train = y[train_indices]

x_test = x[test_indices]
y_test = y[test_indices]

# 3. Scale thickness to improve gradient descent stability
x_train_scaled = x_train / 50.0
x_test_scaled = x_test / 50.0

# 4. Initialise the model parameters
m = 0.0
c = 0.0

learning_rate = 0.1
epochs = 2000

loss_history = []

# 5. Train using gradient descent
for epoch in range(epochs):

    # Make predictions
    predictions = m * x_train_scaled + c

    # Calculate prediction errors
    errors = predictions - y_train

    # Calculate mean squared error
    mse = np.mean(errors ** 2)
    loss_history.append(mse)

    # Calculate gradients
    dm = 2 * np.mean(x_train_scaled * errors)
    dc = 2 * np.mean(errors)

    # Update model parameters
    m -= learning_rate * dm
    c -= learning_rate * dc

# 6. Evaluate on unseen test data
test_predictions = m * x_test_scaled + c
test_mse = np.mean((test_predictions - y_test) ** 2)

print(f"Learned slope (scaled): {m:.4f}")
print(f"Learned intercept: {c:.4f}")
print(f"Training MSE: {loss_history[-1]:.6f}")
print(f"Test MSE: {test_mse:.6f}")

# 7. Plot the loss during training
plt.figure()
plt.plot(loss_history)
plt.xlabel("Epoch")
plt.ylabel("Mean squared error")
plt.title("Gradient Descent Training")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("training_loss.png", dpi=300)
plt.close()

# 8. Plot the model against the test data
x_line = np.linspace(0, 50, 200)
y_line = m * (x_line / 50.0) + c

plt.figure()
plt.scatter(x_train, y_train, s=15, alpha=0.4,
            label="Training data")
plt.scatter(x_test, y_test, s=25,
            label="Test data")
plt.plot(x_line, y_line, label="Linear regression")

plt.xlabel("Concrete thickness (cm)")
plt.ylabel("Detector flux (arbitrary units)")
plt.title("Linear Regression: Synthetic Shielding Data")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("linear_regression.png", dpi=300)
plt.close()

print("Plots saved successfully.")
