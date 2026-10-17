# Pikes Peak for DiRT Rally 2.0

**Unofficial Community Port · Early Preview v0.6.0**

*A classic climb. A new home.*

Experience the iconic Pikes Peak stage from DiRT Rally in DiRT Rally 2.0 — from forest-lined roads to exposed mountain slopes and sweeping views.

This work-in-progress port includes fixes for disappearing trees, pre-start cameras and the vehicle setup scene. A Windows installer provides compatibility checks, verified backups and restoration.

## Download and install

Download the ZIP from [Releases](https://github.com/iam3dev/pikes-peak-dr2/releases), then extract **all** files before running `PikesPeakSetup.exe`. Python is not required to use the installer.

1. Close DiRT Rally 2.0.
2. **Game folder:** select the existing installation containing `dirtrally2.exe`.
3. **Backup folder:** choose where to save the original files. Another drive is supported. Keep this folder for restoration.
4. Click **Check compatibility**, then **Install mod**.
5. Start with a dry daytime event on the replaced Spain route.

This is a **replacement for the supported Spain route**, not a separate location in the menu. The installer rejects unknown map versions. Keep `manifest.json` and `map-payload.bin` beside the executable.

## Restore

Close the game, choose the same game and backup folders, then click **Restore backup**. The button is enabled only after the backup and current installation pass validation.

Restoration returns the state before this installation. A tree fix that was already present is retained. Installing over an already recognised mod does not create a stock Spain backup. Backups created by older tools are not imported automatically.

If an operation fails, preserve its backup folder, `pending.json` and any `.pikes-next` files for diagnosis. Do not force-close the installer while it is writing files.

## Storage

For a fresh supported installation:

- Original Spain backup: approximately **2.35 GB**.
- Original tree-settings blocks: **2,556 bytes** total, only if changed.
- Temporary validated archives on the game drive: up to **6.24 GB**.

Free space is calculated per drive, with 256 MiB headroom per affected volume. Existing fixes reduce the required work. Restoration also keeps a safety copy of the outgoing map. The game executable, vehicles, ReShade and observer are not modified by this installer.

## Known issues and limitations

- Terrain and landscape shading around **11 km** need improvement.
- Distant trees can visibly pop into view; the disappearance fix does not eliminate all pop-in.
- Complete route validation is pending. The analysed run reached about **11.2 km of the 19.5 km route**.
- Other weather conditions, times of day and event modes have not been systematically validated.
- Online, multiplayer and leaderboard behaviour have not been validated.
- A second-PC installation and controlled performance/memory benchmarks remain pending.
- Mods editing the same map or tree-settings blocks may conflict.

## Validation status

- User confirmed installation and gameplay on the primary PC.
- User confirmed the restoration test worked.
- Automated installation/restoration on isolated full-size archives restored the original hashes.
- Tests cover compact block backups, preservation of unrelated edits, rollback after an injected commit failure, and restore-button eligibility.
- GUI compatibility check passed with 200% Windows scaling.

These checks do not establish full-route, all-weather or cross-PC compatibility.

## Feedback

Include your game version, event/weather settings, distance along the route, and a screenshot or short video. For installer errors, include the activity log without personal paths or account details.

## Development

The repository contains the installer source and resource manifest. The large map payload is distributed as a release asset, not committed to Git. It reconstructs the tested mod archive from the supported original Spain archive; it is not a reproducible source pipeline for porting all original track assets.

To build the Windows GUI, use Python 3.12:

```powershell
python -m pip install -r requirements-build.txt
python -m PyInstaller --noconfirm --onefile --windowed --name PikesPeakSetup PikesSetup.py
```

Put `manifest.json` and `map-payload.bin` from the release beside `dist/PikesPeakSetup.exe`.

Run `python test_backup.py` and `python test_compact_backup.py` from a fresh checkout on Windows. The tests create local fixture folders and do not modify a real game installation. The compact-backup test disables the running-game guard only inside its isolated test harness.

## Credits

Original Pikes Peak stage and game assets: **Codemasters / DiRT Rally**.

**Special thanks to Samurai for your support and for believing in this project.**

This is an unofficial fan project, not affiliated with or endorsed by Codemasters or EA. Original game assets retain their respective ownership.
