# engineering/ — hardware reference

## hardware/

Arduino sketches. Each sketch keeps its own folder because the Arduino IDE
requires the folder name to match the `.ino` file name.

| Sketch | Board | Notes |
|---|---|---|
| `TinyPico-Code/SPVVVECTR-MCU-PP-BLE/` | TinyPico (ESP32) | **Current build.** Pulse-period RPM, BLE comms. Flash this to each strut before running the Python BLE code. |
| `TinyPico-Code/SPVVVECTR-MCU-V3/` | TinyPico (ESP32) | Earlier revision. |
| `TinyPico-Code/SPVVVECTR-MCU-PP-BT/` | TinyPico (ESP32) | Classic Bluetooth variant, pulse-period RPM. |
| `TinyPico-Code/SPVVVECTR-MCU-PC-BT/` | TinyPico (ESP32) | Classic Bluetooth variant, pulse-count RPM. |
| `TinyPico-Code/SPVVVECTR-BLE-PP-ProperPI/` | TinyPico (ESP32) | PI speed controller, corrected integral term. |
| `TinyPico-Code/SPVVVECTR-BLE-PP-FlawedPI/` | TinyPico (ESP32) | PI controller with the original (flawed) integral term, kept for comparison. |
| `TinyPico-Code/SPVVVECTR_ProperPI_CodeForTesting/` | TinyPico (ESP32) | Bench-test harness for the corrected PI controller. |
| `TinyPico-Code/SPVVVECTR_FlawedPI_CodeForTesting/` | TinyPico (ESP32) | Bench-test harness for the flawed PI controller. |
| `TinyPico-Code/SPVVVECTR-BLE-PWM/` | TinyPico (ESP32) | Direct PWM control, no closed-loop RPM. |
| `TinyPico-Code/MPU_Resonant_Frequency/` | TinyPico (ESP32) | MPU resonant-frequency sweep. Output in `../data/hardware-characterization/`. |
| `XIAO32C6-Code/SPVVVECTR_XIAO_BLE/` | Seeed XIAO ESP32-C6 | BLE port to the XIAO board. PI control, 12-bit PWM. |
| `XIAO32C6-Code/test_code/` | Seeed XIAO ESP32-C6 | Minimal board bring-up sketch. |
| `Read_RPM/` | any | Standalone RPM-sensor read test. |

## reference/

- `MacAddr&UUID.txt` — BLE MAC address of each of the three struts. The Python
  code in `../software/` matches struts by these addresses.
