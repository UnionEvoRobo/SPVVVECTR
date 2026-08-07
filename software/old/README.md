# legacy/

First-pass scripts, superseded by the modules in `../`. Kept because they are
smaller and easier to read when learning the protocol, and because the Classic
Bluetooth path is still usable if BLE is unavailable.

- `BLE_Scanner.py` — bare-minimum scan for nearby BLE devices.
- `BLE_Read_PWM.py` — connect to one strut and read its PWM/RPM notifications.
- `Simple_BLE_Control.py` — the original single-file BLE control GUI.
- `ClassicBT_Control.py` — Classic Bluetooth (serial) version. Needs 3 free COM ports.
- `test.py` — scratch harness for `SPVVVECTR_Class`.
- `tkinter-examples/` — unrelated Tkinter reference snippets kept from early GUI work.
