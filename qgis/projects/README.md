# QGIS projects

> **Note:** The `qgis/projects/` directory is vestigial — the actual project file
> lives one level up:
>
> `qgis/reiseplan.qgs`
>
> This directory can be ignored.

## Quick reference

- The project is **opened and saved directly in QGIS**.
- When saving, enable **relative paths**:
  *Project → Properties → General → Paths: relative*
- Load styles with **All Categories** before saving so that Map Tips are
  embedded in the `.qgs`.
- For the QField export: `uv run reiseplan-cli build-qfield`
  (builds `qfield/current/{reiseplan.qgz, reiseplan.gpkg}`)

Full setup guide: [../../docs/getting-started/qgis-setup.md](../../docs/getting-started/qgis-setup.md)
