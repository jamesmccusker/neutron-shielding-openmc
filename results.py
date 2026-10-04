import openmc
import csv
import glob


# --------------------------------------------------
# Read attenuation results
# --------------------------------------------------

results = []

for folder in sorted(glob.glob("attenuation_*cm")):

    thickness = float(folder.replace("attenuation_", "").replace("cm", ""))

    statepoint_file = glob.glob(f"{folder}/statepoint.*.h5")[0]

    sp = openmc.StatePoint(statepoint_file)

    tally = sp.get_tally(name="Neutron flux")

    flux = tally.mean.flatten()[0]
    uncertainty = tally.std_dev.flatten()[0]

    results.append((thickness, flux, uncertainty))

    sp.close()


# --------------------------------------------------
# Calculate transmission
# --------------------------------------------------

reference_flux = results[0][1]

results_with_transmission = []

for thickness, flux, uncertainty in results:

    transmission = flux / reference_flux

    results_with_transmission.append((thickness, flux, uncertainty, transmission))


# --------------------------------------------------
# Print results
# --------------------------------------------------

print("\nAttenuation results:\n")

for thickness, flux, uncertainty, transmission in results_with_transmission:

    print(f"{thickness:.1f} cm: " f"Flux = {flux:.6g} +/- {uncertainty:.3g}, " f"Transmission = {transmission:.6g}")

# --------------------------------------------------
# Save results to CSV
# --------------------------------------------------

with open("attenuation_results.csv", "w", newline="") as file:

    writer = csv.writer(file)

    writer.writerow(["thickness_cm", "flux", "uncertainty", "transmission"])

    writer.writerows(results_with_transmission)
