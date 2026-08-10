# analysis/

No robot or motion-capture system required. **make sure file paths are right.**

- `visualization_bo_skopt.ipynb` — loads BO result CSVs and saved GP models
  (`.pkl`) from `../../data/` and plots.
  
- `variance_calculation.py` — computes the baseline noise variance from
  hand-entered displacement measurements. Not really used anymore since entering manual noise in GP was messing w/ plotting `.pkl` data. 
