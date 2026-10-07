# Neutron Shielding Analysis with OpenMC

A Python-based Monte Carlo neutron transport project using [OpenMC](https://openmc.org/) to investigate the effects of shielding material, thickness and layer order on neutron transport to a detector region.

The project was developed as a practical exercise in radiation transport modelling, simulation automation and analysis of Monte Carlo results. It is intended as a simplified computational study, **not** a validated shielding design or nuclear safety assessment.

## Project overview

The model represents a monoenergetic neutron source, an air region, a shielding region and a detector region. The shielding region can contain either one material or multiple layers. Neutron flux is estimated using an OpenMC tally applied to the detector cell.

```text
Neutron source  --->  [ Shielding material(s) ]  --->  Detector region
                       (variable thickness)          (flux tally)
```

The program supports two analysis modes:

1. **Material attenuation:** run a series of simulations for one material at different shield thicknesses and calculate transmission relative to an unshielded reference.
2. **Multilayer shielding:** specify a sequence of shielding materials and their thicknesses, then calculate the detector tally for that configuration.

The material definitions currently include **concrete, water, steel and air**. The selectable shielding materials are concrete, water and steel.

## Methodology

### 1. Material attenuation

The user selects a shielding material, a maximum thickness and a thickness increment. The program runs a fixed-source OpenMC calculation for each thickness, including a zero-thickness reference case.

For each successful run, the program records the detector-cell flux tally estimate and its Monte Carlo statistical uncertainty. It then calculates transmission as

$$
T(x) = \frac{\phi(x)}{\phi(0)}
$$

where:

- $T(x)$ is the dimensionless transmission ratio for shield thickness $x$;
- $\phi(x)$ is the detector-cell flux tally estimate with shielding;
- $\phi(0)$ is the corresponding estimate for the unshielded reference.

The ratio is useful for comparing the response across different shielding thicknesses under the same source and tally definitions.

### 2. Multilayer shielding

The user selects the number of shielding layers, the material in each layer and its thickness. The model then runs a single transport calculation and reports the detector-cell flux tally estimate and its statistical uncertainty.

This mode allows the influence of layer composition and ordering to be explored, although a systematic comparison requires running multiple configurations.

## Results

Example results from a material attenuation study are shown below.

![Neutron flux tally versus shielding thickness](figures/flux_vs_thickness.png)

![Neutron transmission versus shielding thickness](figures/transmission_vs_thickness.png)

The transmission plot uses a logarithmic vertical axis to make changes over a wider range of transmission values easier to see. Error bars represent the estimated Monte Carlo statistical uncertainty; they may be difficult to distinguish from the markers when relative uncertainties are small.

The attenuation mode also writes `attenuation_results.csv`, containing the material, thickness, flux tally estimate, statistical uncertainty, transmission and propagated transmission uncertainty. Individual simulation outputs are stored in folders named for the tested thicknesses (for example, `attenuation_10.0cm`).

**Interpretation of flux:** the detector result is an OpenMC cell flux tally, normalised per source particle. It should not be interpreted as an absolute flux in neutrons/cm²/s without appropriate volume and source-strength normalisation. In particular, a cell-integrated tally is not the same as a volume-averaged flux.

## Statistical uncertainty

OpenMC uses Monte Carlo sampling, so its tally estimates have statistical uncertainty. The project records the standard deviation reported for the tally and, for the attenuation analysis, propagates uncertainty through the ratio of shielded and reference tally estimates.

For independent, nonzero estimates, the usual first-order approximation is

$$
\sigma_T \approx T\sqrt{\left(\frac{\sigma_x}{\phi(x)}\right)^2 + \left(\frac{\sigma_0}{\phi(0)}\right)^2}
$$

where $\sigma_x$ and $\sigma_0$ are the estimated statistical uncertainties in the shielded and reference tallies. This expression assumes independent estimates and is not suitable for zero-valued tallies without additional handling.

These uncertainties describe **Monte Carlo sampling error only**. They do not include uncertainty in geometry, material composition, source specification, nuclear data or other modelling assumptions. For the zero-thickness reference divided by itself, transmission is exactly 1 by definition; its uncertainty should not be interpreted using an independent-ratio formula.

## Running the model

### Requirements

- Python and a working OpenMC installation
- NumPy and Matplotlib
- A compatible OpenMC continuous-energy nuclear data library

See [`requirements.txt`](requirements.txt) for the repository's listed Python dependencies. OpenMC and its native dependencies may require installation through a compatible Conda environment or a separate build.

The nuclear data library is **not included** in this repository. Set `OPENMC_CROSS_SECTIONS` to the location of your cross-section index file, for example:

```bash
export OPENMC_CROSS_SECTIONS="/path/to/cross_sections.xml"
```

From the project directory, activate the environment containing OpenMC and run:

```bash
python model.py
```

The program prompts you to select analysis mode **1** (material attenuation) or **2** (multilayer shielding), followed by the relevant materials and thicknesses.

The source energy, particle histories, batches and several geometry dimensions can be changed in the parameter section at the top of `model.py`. The attenuation mode produces a CSV and displays plots; the multilayer mode prints the detector tally result in the terminal.

**Note:** the attenuation mode recreates run directories for matching thickness values. Back up any results you wish to keep before rerunning the same cases.

## Repository structure

| File or directory | Purpose |
| --- | --- |
| `model.py` | Main program, user inputs, simulation runs and result collection |
| `geometry.py` | Defines the transport geometry and detector cell |
| `materials.py` | Defines air and shielding materials |
| `settings.py` | Configures source and Monte Carlo run settings |
| `tallies.py` | Defines the detector flux tally |
| `plot.py` | Plots attenuation and transmission results |
| `results.py` | Standalone utility for reading attenuation statepoint results |
| `figures/` | Example result figures |
| `requirements.txt` | Listed Python dependencies |

## Assumptions and limitations

- The model uses a simplified, hypothetical geometry rather than a specific facility or engineered shielding arrangement.
- The neutron source is monoenergetic, with its energy specified in the model parameters.
- Calculations use fixed-source Monte Carlo transport.
- Materials use representative compositions rather than verified, application-specific material specifications.
- The outer boundaries are vacuum boundaries, so particles crossing them leave the model.
- The detector is represented by a tally region, not a detailed instrument response model.
- The model has not been benchmarked against experimental measurements or an independently validated reference solution.
- Only Monte Carlo statistical uncertainty is reported; broader modelling and nuclear-data uncertainties have not been quantified.

Results should therefore be interpreted as an exploratory comparison of simplified shielding configurations, **not as design values or evidence of regulatory compliance**.

## Potential extensions

Future work could include systematic parameter sweeps, additional source energy distributions, comparison with reference attenuation cases, improved handling of zero or very low tally values, and a machine-learning surrogate trained on independently generated OpenMC simulation data.
