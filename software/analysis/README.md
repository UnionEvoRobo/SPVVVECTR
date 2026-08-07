# analysis/

Offline — no robot or motion-capture system required.

- `visualization_bo_skopt.ipynb` — loads BO result CSVs and saved GP models
  (`.pkl`) from `../../data/` and plots convergence and partial dependence.
- `variance_calculation.py` — computes the baseline noise variance from
  hand-entered displacement measurements.
