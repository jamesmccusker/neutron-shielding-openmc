import pandas as pd
import matplotlib.pyplot as plt

# Load the dataset
data = pd.read_csv("synthetic_data.csv")

# Extract the variables
thickness = data["thickness_cm"]
flux = data["detector_flux"]

# Plot the data
plt.scatter(thickness, flux, s=15)

plt.xlabel("Concrete thickness (cm)")
plt.ylabel("Detector flux (arbitrary units)")
plt.title("Synthetic Neutron Attenuation Data")

plt.grid(alpha=0.3)
plt.tight_layout()

plt.savefig("synthetic_data.png", dpi=300)
plt.show()
