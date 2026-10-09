import numpy as np
import pandas as pd

# Set random seed for reproducibility
rng = np.random.default_rng(42)

# Generate 100 random shielding thicknesses (cm)
n_samples = 100
thickness = rng.uniform(0, 50, n_samples)

# Simplified exponential attenuation model
initial_flux = 1.0
attenuation_coefficient = 0.08  # cm^-1

true_flux = initial_flux * np.exp(
    -attenuation_coefficient * thickness
)

# Add a small amount of random measurement-like noise
noise = rng.normal(0, 0.02, n_samples)

detector_flux = np.maximum(true_flux + noise, 0)

# Create dataset
data = pd.DataFrame({
    "thickness_cm": thickness,
    "detector_flux": detector_flux
})

# Save dataset
data.to_csv("synthetic_data.csv", index=False)

print(data.head())
print(f"\nGenerated {len(data)} samples.")
