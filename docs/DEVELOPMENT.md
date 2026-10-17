# Development

The repository contains the installer source and resource manifest. It reconstructs the tested mod archive from the supported original Spain archive; it is not a reproducible source pipeline for porting all original track assets.

To build the Windows GUI, use Python 3.12:

```powershell
python -m pip install -r requirements-build.txt
python -m PyInstaller --noconfirm --onefile --windowed --name PikesPeakSetup PikesSetup.py
```

Put `manifest.json` and `map-payload.bin` from the release beside `dist/PikesPeakSetup.exe`.

Run `python test_backup.py` and `python test_compact_backup.py` from a fresh checkout on Windows. The tests create local fixture folders and do not modify a real game installation. The compact-backup test disables the running-game guard only inside its isolated test harness.

