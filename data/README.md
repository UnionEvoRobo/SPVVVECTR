# data/ — experiment results

Read-only record of what the robot did. Nothing here is generated at import
time; the scripts in `../software/` write new results to their working
directory and they get filed here afterwards.

Most subfolders carry a `read.md` describing that specific run — read those
first.

| Folder | What it holds |
|---|---|
| `initial-data-no-api/` | Earliest recordings, made before the motion-capture API was wired in. Raw CSV/TSV strut telemetry. |
| `bo_experiment_SPVVVECTR-1a/` | First Bayesian-optimization campaign, comparing three prior strategies: `bo_results_lhs_priors/`, `bo_results_random_priors/`, `bo_results_no_priors/`. |
| `bo_experiment_SPVVVECTR-1b/` | Second campaign. `lhs/` holds the two dated LHS+BO experiments, `benchmark_testing/` compares the optimized gait against a linear gait, `randoms_occasional_repositioning/` covers the repositioning study. |

## File types

- `bo_results_*.csv` — one row per trial: RPM triple and measured displacement.
- `bo_model_*.pkl` — pickled scikit-optimize result (the fitted Gaussian process).
  Load with `skopt.load`.
- `variance_results_*.csv` — repeat trials of a single RPM triple, for noise estimation.

`../software/analysis/visualization_bo_skopt.ipynb` reads these paths directly.
