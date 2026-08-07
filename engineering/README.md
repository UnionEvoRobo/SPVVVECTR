# engineering/ — embedded firmware and hardware reference

What runs *on the robot*, as opposed to `../software/`, which runs on the laptop.

## firmware/

Arduino sketches. Each sketch keeps its own folder because the Arduino IDE
requires the folder name to match the `.ino` file name.

| Sketch | Board | Notes |
|---|---|---|
| `TinyPico-Code/SPVVVECTR-MCU-PP-BLE/` | TinyPico (ESP32) | **Current build.** Pulse-period RPM, BLE comms. Flash this to each strut before running the Python BLE code. |
| `TinyPico-Code/SPVVVECTR-MCU-V3/` | TinyPico (ESP32) | Earlier revision. |
| `TinyPico-Code/SPVVVECTR-MCU-PP-BT/` | TinyPico (ESP32) | Classic Bluetooth variant, pulse-period RPM. |
| `TinyPico-Code/SPVVVECTR-MCU-PC-BT/` | TinyPico (ESP32) | Classic Bluetooth variant, pulse-count RPM. |
| `XIAO32C6-Code/SPVVVECTR_XIAO_BLE/` | Seeed XIAO ESP32-C6 | BLE port to the XIAO board. |
| `XIAO32C6-Code/test_code/` | Seeed XIAO ESP32-C6 | Minimal board bring-up sketch. |
| `Read_RPM/` | any | Standalone RPM-sensor read test. |

## reference/

- `MacAddr&UUID.txt` — BLE MAC address of each of the three struts. The Python
  code in `../software/` matches struts by these addresses.
