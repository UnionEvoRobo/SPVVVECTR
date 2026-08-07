# software/ — host-side Python

Everything that runs on the laptop. The microcontroller code it talks to lives
in `../engineering/firmware/`; the data it produces lives in `../data/`.

## Layout

| Path | What it is |
|---|---|
| `Strut_Class.py` | `Strut` — BLE connection + control for one PCB strut. |
| `SPVVVECTR_Class.py` | `SPVVVECTR` — the whole 6-bar / 3-PCB robot. Wraps three `Strut`s, handles CSV recording. |
| `spvvvectr_tracker.py` | `QtmTracker` — Qualisys motion-capture client, gives robot position. |
| `SPVVVECTR_GUI_Control.py` | Tkinter control panel. **Start here to drive the robot by hand.** |
| `bo_skopt.py` | Bayesian optimization of the gait (scikit-optimize). Main experiment driver. |
| `better_variance_recording.py` | Repeats one RPM combo N times to measure run-to-run variance. |
| `analysis/` | Offline analysis — no hardware needed. Notebook + variance math. |
| `tools/` | Small standalone utilities (BLE signal-strength check). |
| `legacy/` | Superseded first-pass scripts, kept for reference. Not maintained. |

These six top-level modules import each other as flat siblings, so they must
stay in this directory together.

## Running

```bash
pip install -r ../requirements.txt
python SPVVVECTR_GUI_Control.py     # manual control + recording
python bo_skopt.py                  # gait optimization (needs robot + Qualisys)
```

Scripts write their CSV/PKL output to the current working directory. Run them
from wherever you want the results to land, then file the results under
`../data/`. The GUI has a "select working directory" button for the same purpose.

The optimization scripts expect a Qualisys server at `10.76.30.85` (hardcoded in
`bo_skopt.py` and `better_variance_recording.py`) and the strut MAC addresses in
`../engineering/reference/MacAddr&UUID.txt`.
