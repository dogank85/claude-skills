---
name: documentation-manager
description: Automates project documentation maintenance (Changelog, ADRs, Status).
version: 1.0.0
---

# Documentation Manager

This skill helps maintain a healthy documentation state for the project by automating the creation and updating of key documentation files.

## Tools

### `log_change`
Appends a new entry to `CHANGELOG.md` under today's date.

**Usage:**
```bash
python3 scripts/log_change.py "Fixed the login bug" --type fix
```

### `create_adr`
Creates a new Architecture Decision Record (ADR) in `docs/adr/`.

**Usage:**
```bash
python3 scripts/new_adr.py "Move logs to project root"
```

### `update_status`
Updates the central `PROJECT_STATUS.md` file.

**Usage:**
```bash
python3 scripts/update_status.py "Focusing on mobile UI polish" --blockers "None"
```
