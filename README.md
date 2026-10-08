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

# Running the calibration workflows
All commands below are run from the FASMID root folder (the folder containing this README), in a Python environment with numpy, scipy, pandas and PyYAML.

## Calibrator
The Calibrator takes a calibration file (Calibration/Calibration_Files/NewCal<model>.py) and a YAML config that lists the free variables, the targets and the solver options. Its equations follow Model-Solver VersionB3.py, and its scenario switches default to the values set in SolveandStore.py.

```bash
python -m Calibrator validate --config calibrator.yaml
python -m Calibrator solve --config calibrator.yaml --out NewCalREMIND2022_solved.py
```

`validate` evaluates the calibration file as it stands and prints the stock-flow residuals (NLP_TOTAL, CAR_identity, ...) and the targets. `solve` moves the free variables until the hard residuals are closed and the targets are met. It then writes the solved calibration file, a `.diff.txt` listing the values that changed, and a `.report.json`. If the solution fails validation, the same three files are written with a `_failed` suffix. Without `--out`, the file is written as NewCal<model>_calibrated.py in the current folder. Check the diff before copying values into a NewCal<model>.py file.

A minimal config:

```yaml
model: REMIND2022
globals: {bubble: 1}
overrides:
  mu_X: {role: FREE, lo: 0.3, hi: 1.5}
  mu_K: {role: FREE, lo: 2.0, hi: 8.0}
  w: {role: FREE, lo: 0.001, hi: 0.003}
  xiDiv_HC: {role: FREE, lo: 0.2, hi: 0.9}
targets:
  WShare: {value: 0.49, tol: 0.01, kind: eq}
options:
  hard_residuals: [NLP_TOTAL, CAR_identity]
  multistart: 3
```

Target kinds are `soft`, `eq`, `ineq_geq` and `ineq_leq`. Setting `equation_source: versionb3` under `options` evaluates one period of Model-Solver VersionB3.py instead of the Calibrator's own equation library.

## CMAESCalibrator
Each Current policy baseline has its own config in Calibration/Configs. It sets the parameters and their bounds, the targets, the CMA-ES settings and the output paths.

| Configs | Baselines |
|---|---|
| scen1.yaml, scen2.yaml, scen3.yaml | GCAM, MESSAGE, REMIND |
| scen21.yaml, scen22.yaml, scen23.yaml | GCAM2021, MESSAGE2021, REMIND2021 |
| scen39.yaml, scen40.yaml, scen41.yaml | GCAM2022, MESSAGE2022, REMIND2022 |

For one baseline (here REMIND2022):

```bash
python -m CMAESCalibrator validate --config Calibration/Configs/scen41.yaml
python -m CMAESCalibrator run --config Calibration/Configs/scen41.yaml
python apply_best_calibrations.py --variants REMIND2022
```

`validate` checks the config and runs one simulation at the midpoint of the parameter bounds; add `--no-dry-run` to skip that simulation. `run` launches the CMA-ES search. The evaluation history goes to Calibration/History and the best parameter set to Calibration/Results/cmaes_best_<model>.json. Each evaluation runs the full model, and the configs use 72 parallel workers (`cmaes.workers`); lower that value on a smaller machine.

apply_best_calibrations.py writes the best parameters, truncated to two decimals, into Calibration/Calibration_Files/NewCal<model>_Calibrated.py, together with a `.changes.txt` listing the changed values. The base NewCal<model>.py file is left untouched. Without `--variants`, it applies every baseline that has a result. SolveandStore.py and the experiment scripts read the `_Calibrated` files.

Launchers/CMAES_FASMID_2020.sh, CMAES_FASMID_2021.sh and CMAES_FASMID_2022.sh submit this sequence for one vintage each as LSF jobs. In these launchers the REMIND `run` lines are commented out, so only the GCAM and MESSAGE parameters are re-estimated before apply_best_calibrations.py runs.
