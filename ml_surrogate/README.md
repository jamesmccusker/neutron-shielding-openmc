### Cross-Validation Results

To evaluate the surrogate models beyond a single train/test split, leave-one-interior-thickness-out cross-validation was performed on 16 OpenMC simulation results spanning 0–30 cm of concrete shielding.

Each of the 14 intermediate shielding thicknesses was withheld in turn, with the remaining 15 configurations used for training. The 0 cm and 30 cm endpoints were retained in every training set to evaluate interpolation rather than extrapolation.

| Model                            | Mean Absolute Percentage Error |     R² |
| -------------------------------- | -----------------------------: | -----: |
| Log-linear Regression            |                          6.87% | 0.9946 |
| Polynomial Regression (Degree 3) |                      **3.38%** | 0.9934 |
| Random Forest                    |                         137.3% | 0.1227 |

Cubic polynomial regression achieved the lowest relative prediction error, demonstrating its ability to approximate the nonlinear attenuation behaviour observed in the OpenMC simulations.

Log-linear regression also performed well, offering a simpler, physically motivated representation of neutron attenuation. Random forest regression produced substantially larger relative errors, reflecting the limitations of tree-based models when learning a smooth relationship from a small dataset.

**Limitations:** The surrogate is currently restricted to a single shielding material, source energy and simulation geometry. Validation covers interpolation within the 0–30 cm training range, and the underlying Monte Carlo results contain statistical uncertainties. Further testing would be required before using the model for engineering predictions outside this domain.
