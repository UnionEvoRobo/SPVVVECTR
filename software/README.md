# software/

## Layout

| Path | What it is |
|---|---|
| `Strut_Class.py` | `Strut` — BLE connection + control for one PCB strut. |
| `SPVVVECTR_Class.py` | `SPVVVECTR` — the whole 6-bar / 3-PCB robot. Wraps three `Strut`s, handles CSV recording. |
| `spvvvectr_tracker.py` | `QtmTracker` — Qualisys motion-capture client, gives robot position. |
| `SPVVVECTR_GUI_Control.py` | Tkinter control panel. **Start here to drive the robot by hand.** |
| `bo_skopt.py` | Bayesian optimization of the gait (scikit-optimize). Main experiment driver. |
| `better_variance_recording.py` | Repeats one RPM combo N times to measure run-to-run variance. |
| `analysis/` | Analysis of data from `.csv`/`.pkl` files. |
| `tools/` | Small standalone utilities (BLE signal-strength check). |
| `legacy/` | Old scripts not used, kept for reference. |


## Running

```bash
pip install -r ../requirements.txt
python SPVVVECTR_GUI_Control.py     # manual control + recording
python bo_skopt.py                  # gait optimization (needs robot + Qualisys)
```

Scripts write their CSV/PKL output to current working directory. Move the results under `../data/`. The GUI has a "select working directory" that does the same thing. 

The optimization scripts expect a Qualisys server at `10.76.30.85` and the strut MAC addresses in `../engineering/reference/MacAddr&UUID.txt`.
