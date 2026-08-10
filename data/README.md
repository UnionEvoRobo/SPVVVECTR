# data/ — experiment results

What the robot did after running programs in `/software` directory. Subfolders in this directory have `read.md` w/ specific experiment details.

| Folder | What it holds |
|---|---|
| `initial-data-no-api/` | Initial data before qtm api was integrated. |
| `bo_experiment_SPVVVECTR-1a/` | First Bayesian-optimization trials w/ first iteration of spvvvectr (lighter body) that compared three prior strategies: `bo_results_lhs_priors/`, `bo_results_random_priors/`, `bo_results_no_priors/`. |
| `bo_experiment_SPVVVECTR-1b/` | Second trials with rebuilt spvvvectr (thicker springs; heavier body). `lhs/` holds two LHS-Priors + BO experiments, `benchmark_testing/` compares BO gaits against pre-determined baselines, `randoms_occasional_repositioning/` tests effects of repositioning the robot after every trial / occasionally. |
| `variance_record/` | Repeat-trial variance runs recorded with yaw, from the qtm-api-integration work. |
| `hardware-characterization/` | Bench measurements of the hardware itself (MPU resonance, PWM-to-RPM), not locomotion trials. |

## File types

- `.csv` — records RPM inputs and measured displacement.
- `.pkl` — trained optimizer model (w/ sci-kit optimize).
- `variance_results_*.csv` — repeat trials of a single RPM triple, for noise estimation.
`.ipynb` - data visualization + interpretation
