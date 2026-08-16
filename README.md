# SPVVVECTR — Locomotion Optimization

Microcontroller, BLE, and optimization code for controlling the SPVVVECTR robot
and optimizing its linear displacement.

**Authors:** Miraj Parekh & Duy Hung Dang

## Layout

| Folder | What's in it |
|---|---|
| `software/` | Python control code, Bayesian optimization, and analysis. |
| `engineering/` | Arduino firmware for the struts, plus hardware reference. |
| `data/` | Experiment results (CSV, PKL) with notes per experiment. |

Each folder has its own README with details.

## Quick start

1. Flash `engineering/firmware/TinyPico-Code/SPVVVECTR-MCU-PP-BLE/` to each of
   the three struts.
2. Run the Python code **from inside `software/`**:

```bash
pip install -r requirements.txt
cd software
python SPVVVECTR_GUI_Control.py # manual control + recording
python bo_skopt.py              # gait optimization (needs Qualisys)
```

*Also see `Summer_2026_Research_Report.pdf` for a detailed overview of our project and results* 


