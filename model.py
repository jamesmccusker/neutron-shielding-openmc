import openmc
import csv
import shutil
import argparse
import math
from pathlib import Path

from materials import create_materials
from geometry import geometry
from tallies import create_tallies
from settings import create_settings
from plot import plot

# Command-line arguments for automated simulations
parser = argparse.ArgumentParser(
    description="OpenMC neutron shielding model"
)

parser.add_argument(
    "--material",
    type=str,
    default=None
)

parser.add_argument(
    "--max-thickness",
    type=float,
    default=None
)

parser.add_argument(
    "--step",
    type=float,
    default=None
)

args = parser.parse_args()

automated_mode = args.material is not None

if automated_mode:
    if args.max_thickness is None or args.step is None:
        parser.error(
            "Automated mode requires --max-thickness and --step"
        )

    if not (
        math.isfinite(args.max_thickness)
        and math.isfinite(args.step)
        and args.max_thickness > 0
        and args.step > 0
    ):
        parser.error(
            "Thickness values must be finite and positive"
        )
# ==================================================
# Model parameters
# ==================================================

# --------------------------------------------------
# Physical geometry parameters
# --------------------------------------------------

shield_height = 5              # cm
source_distance = 1            # cm
detector_gap = 1               # cm
detector_thickness = 1         # cm
air_before = 2                 # cm
air_after = 10                 # cm


# --------------------------------------------------
# Source parameters
# --------------------------------------------------

source_energy = 1.0            # MeV


# --------------------------------------------------
# Monte Carlo parameters
# --------------------------------------------------

particles = 100000
batches = 55


# ==================================================
# Create material library
# ==================================================

materials = create_materials()

air = materials["air"]

shielding_materials = [
    name for name in materials
    if name != "air"
]

print("Available shielding materials:")

for name in shielding_materials:
    print("-", name)


# ==================================================
# Select analysis
# ==================================================

if automated_mode:
    analysis_type = "1"

else:
    print("\nSelect analysis:")
    print("1 - Material attenuation")
    print("2 - Multilayer shielding")

    while True:

        analysis_type = input("\nEnter analysis number: ").strip()

        if analysis_type in ["1", "2"]:
            break

        print("Invalid selection. Please enter 1 or 2.")


# ==================================================
# MATERIAL ATTENUATION
# ==================================================

if analysis_type == "1":

    print("\nSelected: Material attenuation")


    # --------------------------------------------------
    # Select material
    # --------------------------------------------------


    if automated_mode:
        material_name = args.material.strip().lower()
        if material_name not in shielding_materials:
            parser.error(f"Unknown material: {material_name}")

    else:
        while True:

            material_name = input("\nSelect material: ").strip().lower()

            if material_name in shielding_materials:
                break
            print("Invalid material. Please select one of the available shielding materials.")

    selected_material = materials[material_name]

    print(
        f"\nTesting attenuation of "
        f"{selected_material.name}"
    )


    # --------------------------------------------------
    # Select maximum thickness
    # --------------------------------------------------
    if automated_mode:
        maximum_thickness = args.max_thickness
        thickness_step = args.step
    else:

        while True:

            try:

                maximum_thickness = float(
                    input(
                        "What is the maximum thickness (cm)? "
                    )
                )

                if maximum_thickness > 0:
                    break

                print(
                    "Maximum thickness must be greater than 0 cm."
                )

            except ValueError:

                print(
                    "Please enter a valid number."
                )


    # --------------------------------------------------
    # Select thickness step
    # --------------------------------------------------

        while True:

            try:

                thickness_step = float(
                    input(
                        "What would you like the thickness "
                        "step to be (cm)? "
                    )
                )

                if thickness_step > 0:
                    break

                print(
                    "Thickness step must be greater than 0 cm."
                )

            except ValueError:

                print(
                    "Please enter a valid number."
                )


    # --------------------------------------------------
    # Create list of thicknesses
    # --------------------------------------------------

    thickness_values = []

    thickness = 0

    while thickness <= maximum_thickness:

        thickness_values.append(thickness)

        thickness += thickness_step

    print("\nThicknesses to be tested:")
    print(thickness_values)


    # --------------------------------------------------
    # Store attenuation results
    # --------------------------------------------------

    results = []


    # --------------------------------------------------
    # Run attenuation simulations
    # --------------------------------------------------

    for thickness in thickness_values:

        print(
            f"\nRunning {selected_material.name} "
            f"at {thickness} cm..."
        )


        # --------------------------------------------------
        # Define shielding configuration
        # --------------------------------------------------

        selected_materials = [
            selected_material
        ]

        test_thicknesses = [
            thickness
        ]


        # --------------------------------------------------
        # Build geometry
        # --------------------------------------------------

        root_universe, detector_cell = geometry(
            air,
            selected_materials,
            test_thicknesses,
            shield_height,
            source_distance,
            detector_gap,
            detector_thickness,
            air_before,
            air_after
        )

        model_geometry = openmc.Geometry(
            root_universe
        )


        # --------------------------------------------------
        # Create tally
        # --------------------------------------------------

        model_tallies = create_tallies(
            detector_cell
        )


        # --------------------------------------------------
        # Create settings
        # --------------------------------------------------

        model_settings = create_settings(
            source_distance,
            shield_height,
            source_energy,
            particles,
            batches
        )


        # --------------------------------------------------
        # Create OpenMC model
        # --------------------------------------------------

        model = openmc.Model(
            geometry=model_geometry,
            settings=model_settings,
            tallies=model_tallies
        )


        # --------------------------------------------------
        # Create separate folder for simulation
        # --------------------------------------------------

        run_directory = (
            f"attenuation_{thickness}cm"
        )
        # Remove old results from this thickness
        if Path(run_directory).exists():
            shutil.rmtree(run_directory)

        # --------------------------------------------------
        # Run OpenMC
        # --------------------------------------------------

        model.run(
            cwd=run_directory
        )


        # --------------------------------------------------
        # Find statepoint
        # --------------------------------------------------

        statepoint_file = (Path(run_directory) / f"statepoint.{batches}.h5")
        if not statepoint_file.exists():
            print("expected statepoint file was not found.")
            print("skipping this result.")
            continue


        # --------------------------------------------------
        # Read tally result
        # --------------------------------------------------

        with openmc.StatePoint(
            statepoint_file
        ) as sp:

            tally = sp.get_tally(
                name="Neutron flux"
            )

            flux = tally.mean.flatten()[0]

            uncertainty = (
                tally.std_dev.flatten()[0]
            )


        # --------------------------------------------------
        # Store result
        # --------------------------------------------------

        results.append(
            (
                thickness,
                flux,
                uncertainty
            )
        )


        print(
            f"Flux = {flux:.6g} "
            f"+/- {uncertainty:.3g}"
        )


    # ==================================================
    # Calculate transmission
    # ==================================================

    if results:

        # --------------------------------------------------
        # Use the 0 cm result as the reference
        # --------------------------------------------------

        reference_result = next(result for result in results if result[0] == 0)
        reference_flux = reference_result[1]
        reference_uncertainty = reference_result[2]

        print("\nTransmission results:")


        # --------------------------------------------------
        # Create results CSV
        # --------------------------------------------------

        with open(
            "attenuation_results.csv",
            "w",
            newline=""
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "material",
                "thickness_cm",
                "flux",
                "uncertainty",
                "transmission",
                "transmission_uncertainty"
            ])


            # --------------------------------------------------
            # Calculate transmission and write each result
            # --------------------------------------------------

            if reference_flux <= 0:
                raise ValueError("Reference flux must be greater than zero.")

            for thickness, flux, uncertainty in results:

                if thickness == 0:
                    # The reference divided by itself is exactly one.
                    transmission = 1.0
                    transmission_uncertainty = 0.0

                elif flux > 0:
                    transmission = flux / reference_flux
                    transmission_uncertainty = transmission * (
                        (uncertainty / flux) ** 2
                        + (reference_uncertainty / reference_flux) ** 2
                    ) ** 0.5

                else:
                    transmission = 0.0
                    transmission_uncertainty = uncertainty / reference_flux

                print(
                    f"{thickness:.1f} cm: "
                    f"Transmission = {transmission:.6g} "
                    f"+/- {transmission_uncertainty:.3g}"
                )

                writer.writerow([
                    selected_material.name,
                    thickness,
                    flux,
                    uncertainty,
                    transmission,
                    transmission_uncertainty
                ])


        print(
            "\nAttenuation study complete."
        )

        print(
            "Results saved to attenuation_results.csv"
        )


        # --------------------------------------------------
        # Plot results
        # --------------------------------------------------

        if not automated_mode:
            plot()


    else:

        print(
            "\nNo attenuation results were generated."
        )


# ==================================================
# MULTILAYER SHIELDING
# ==================================================

elif analysis_type == "2":

    print("\nSelected: Multilayer shielding")


    # --------------------------------------------------
    # Select number of materials
    # --------------------------------------------------

    while True:

        try:

            number_of_materials = int(
                input(
                    "\nHow many shielding materials "
                    "do you want? "
                )
            )

            if (
                1 <= number_of_materials
                <= len(shielding_materials)
            ):
                break

            print(
                f"Please enter a number between 1 and "
                f"{len(shielding_materials)}."
            )

        except ValueError:

            print(
                "Please enter a whole number."
            )


    selected_materials = []
    material_thicknesses = []


    # --------------------------------------------------
    # Select materials and thicknesses
    # --------------------------------------------------

    for i in range(number_of_materials):


        # --------------------------------------------------
        # Select material
        # --------------------------------------------------

        while True:

            material_name = input(
                f"\nEnter material {i + 1}: "
            ).strip().lower()

            if material_name in shielding_materials:
                break

            print(
                "Invalid material. Please select one of "
                "the available shielding materials."
            )


        # --------------------------------------------------
        # Select thickness
        # --------------------------------------------------

        while True:

            try:

                thickness = float(
                    input(
                        f"Enter thickness of "
                        f"{material_name} (cm): "
                    )
                )

                if thickness > 0:
                    break

                print(
                    "Thickness must be greater than 0 cm."
                )

            except ValueError:

                print(
                    "Please enter a valid number."
                )


        selected_materials.append(
            materials[material_name]
        )

        material_thicknesses.append(
            thickness
        )


    # --------------------------------------------------
    # Display shielding configuration
    # --------------------------------------------------

    print(
        "\nSelected shielding configuration:"
    )

    for i in range(number_of_materials):

        print(
            f"Material {i + 1}: "
            f"{material_thicknesses[i]} cm "
            f"{selected_materials[i].name}"
        )


    total_thickness = sum(
        material_thicknesses
    )

    print(
        f"Total shielding thickness: "
        f"{total_thickness} cm"
    )


    # --------------------------------------------------
    # Build geometry
    # --------------------------------------------------

    root_universe, detector_cell = geometry(
        air,
        selected_materials,
        material_thicknesses,
        shield_height,
        source_distance,
        detector_gap,
        detector_thickness,
        air_before,
        air_after
    )

    model_geometry = openmc.Geometry(
        root_universe
    )


    # --------------------------------------------------
    # Create tally
    # --------------------------------------------------

    model_tallies = create_tallies(
        detector_cell
    )


    # --------------------------------------------------
    # Create settings
    # --------------------------------------------------

    model_settings = create_settings(
        source_distance,
        shield_height,
        source_energy,
        particles,
        batches
    )


    # --------------------------------------------------
    # Create OpenMC model
    # --------------------------------------------------

    model = openmc.Model(
        geometry=model_geometry,
        settings=model_settings,
        tallies=model_tallies
    )


    # --------------------------------------------------
    # Run OpenMC
    # --------------------------------------------------

    print(
        "\nRunning multilayer shielding simulation..."
    )

    model.run(
        cwd="results"
    )


    # --------------------------------------------------
    # Find statepoint
    # --------------------------------------------------

    statepoint_files = list(
        Path("results").glob(
            "statepoint.*.h5"
        )
    )


    if not statepoint_files:

        print(
            "No statepoint file found."
        )

    else:

        statepoint_file = statepoint_files[-1]


        # --------------------------------------------------
        # Read tally result
        # --------------------------------------------------

        with openmc.StatePoint(
            statepoint_file
        ) as sp:

            tally = sp.get_tally(
                name="Neutron flux"
            )

            flux = tally.mean.flatten()[0]

            uncertainty = (
                tally.std_dev.flatten()[0]
            )


        # --------------------------------------------------
        # Display result
        # --------------------------------------------------

        print(
            "\nMultilayer shielding simulation complete."
        )

        print(
            f"Detector neutron flux = "
            f"{flux:.6g}"
        )

        print(
            f"Statistical uncertainty = "
            f"+/- {uncertainty:.3g}"
        )

