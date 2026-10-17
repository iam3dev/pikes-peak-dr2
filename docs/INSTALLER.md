# Installer details

## Storage

For a fresh supported installation:

- Original Spain backup: approximately **2.35 GB**.
- Original tree-settings blocks: **2,556 bytes** total, only if changed.
- Temporary validated archives on the game drive: up to **6.24 GB**.

Free space is calculated per drive, with 256 MiB headroom per affected volume. Existing fixes reduce the required work. Restoration also keeps a safety copy of the outgoing map. The game executable, vehicles, ReShade and observer are not modified by this installer.

## Recovery

Restoration returns the pre-install state. An existing tree fix is retained. Installing over an already recognised mod does not create a stock Spain backup. Backups created by older tools are not imported automatically.

If an operation fails, preserve the backup folder, `pending.json` and any `.pikes-next` files for diagnosis. Do not force-close the installer while it is writing files.

## Validation

- User confirmed installation and gameplay on the primary PC.
- User confirmed the restoration test worked.
- Automated installation/restoration on isolated full-size archives restored the original hashes.
- Tests cover compact block backups, preservation of unrelated edits, rollback after an injected commit failure, and restore-button eligibility.
- GUI compatibility check passed with 200% Windows scaling.

These checks do not establish full-route, all-weather or cross-PC compatibility.

