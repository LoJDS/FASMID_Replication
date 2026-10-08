# Introduction
This repository contains the replication code necessary to reproduce the results in the paper _Financial fragility along the low-carbon transition_.

The repository includes all the codebases needed to replicate the paper's figures and results. Due to space limitations, files and figures were not directly uploaded, but are
available on demand.

# Calibration
Calibration is a two-step process. 

The "Calibrator" workflow solves the model using starting values for some endogenous variables to fit the SFC constraints of FASMID.
It produces a set of starting endogenous variables for the model's learning phase. Currently, the practice has been to work with a pre-existing
calibration and to modify parameters from it instead of re-running the problem each time, by making sure that changes in parameter values and
the addition of new behavioural equations did not breach stock-flow consistency. 

The CMAESCalibrator changes parameter values to fit the endogenous/starting value targets specified in Calibration/Configs for each Current policy baseline.
It uses CMA-ES, a free-derivative algorithm, on a subset of parameters. It yields the best parameter set, which is used to create 
calibration files, stored in the dedicated folder (Calibration/Calibration_Files). The protocol can be run using CMAESCalibrator/Runner.py followed by 
apply_best_calibrations.py.

# Simulations

The main simulations are obtained by running "Solve and Store.py". 

Sensitivity analysis on Carbon prices and Conversion (Appendix D.3.2) can be simulated using Policy_Experiments.py.
Technical bottleneck sensitivity (Appendix D.3.2) can be reproduced by running Bottleneck.py

The financial sector experiments (Appendix F) can be run using Experiments.py

# Model files
Model-Solver VersionA.py is an initialiser file for the fixed-point algorithm

Model-Solver VersionB3.py is the model file used in the solving loop 

# Sensitivity analysis
The workflow is in Sensitivity Analysis, with dedicated model files consistent with the main simulation files

The process requires first creating an LHS sample using LatHyperRemind2022_Parallel2.py. Then, the database for sensitivity intervals and
Optimal-Transport indices is created by running ScenarioRun_Parallel.py. Sobol indices have a distinct workflow, using Sobol.py and Sobol_plot.py,
with sampling bounds consistent with those of the LHS sampling.

# Visualisation 
The visualisation workflow is contained in the Viz folder. The main figures are generated with Figures.R, Sensitvity_Data.R formats 
csvs to generate sensitivity figures with Sensitivity.R. The rest of the files are self-containe,d with self-explanatory names.
