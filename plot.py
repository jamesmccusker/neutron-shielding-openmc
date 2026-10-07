import csv
import matplotlib.pyplot as plt

def plot():
    thickness = []
    flux = []
    uncertainty = []
    transmission = []
    transmission_uncertainty = []

    with open("attenuation_results.csv", "r") as file:
        reader = csv.DictReader(file)

        for row in reader:
            thickness.append(float(row["thickness_cm"]))
            flux.append(float(row["flux"]))
            uncertainty.append(float(row["uncertainty"]))
            transmission.append(float(row["transmission"]))
            transmission_uncertainty.append(
                float(row["transmission_uncertainty"])
            )

    print("Results loaded.")
    print("Thickness:", thickness)
    print("Flux:", flux)
    print("Transmission:", transmission)


    # --------------------------------------------------
    # Plot 1: Neutron flux vs shield thickness
    # --------------------------------------------------

    plt.figure()

    plt.errorbar(
        thickness,
        flux,
        yerr=uncertainty,
        fmt="o",
        markersize=4,
        capsize=0,
        linestyle="none"
    )

    plt.xlabel("Shield thickness / cm")
    plt.ylabel("Cell-integrated neutron flux (cm/source particle)")
    plt.title("Neutron flux vs shield thickness")
    plt.grid()

    plt.show()


    # --------------------------------------------------
    # Plot 2: Neutron transmission vs shield thickness
    # --------------------------------------------------

    plt.figure()

    plt.errorbar(
        thickness,
        transmission,
        yerr=transmission_uncertainty,
        fmt="o",
        markersize=4,
        capsize=0,
        linestyle="none"
    )

    plt.yscale("log")

    plt.xlabel("Shield thickness / cm")
    plt.ylabel("Transmission")
    plt.title("Neutron transmission vs shield thickness")
    plt.grid(True, which="both")

    plt.show()

    return None
