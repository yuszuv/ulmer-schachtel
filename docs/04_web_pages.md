# Online Map via GitHub Pages

This document describes how to build the public-facing website and deploy it to
GitHub Pages. Goal: anyone without QGIS can open a URL and see an interactive
map plus a readable route/destination overview.

## What is shown?

The page (`tools/build_site.py` → `site/index.html`) is **self-contained**:
data is inlined directly, so it also works locally via `file://`. Contents:

- **Interactive map** (Leaflet, OpenStreetMap base) with togglable layers:
  - Route corridors (dashed brown lines) — popup with route and length
  - Rail stations (grey dots)
  - Destinations (shape/colour per category: Dracula town = dark red circle,
    city = sepia square, Danube Delta = teal triangle) — popup with notes
  - Info marker "About this map" — legend and usage notes
- **Route overview** per magistrală with stops and notes
- **Destinations** grouped by category

The overview text is server-side-rendered and readable without JavaScript.

## Build locally

```bash
python tools/build_site.py            # generates ./site/index.html
python tools/build_site.py --out _out # alternative output directory
```

The source remains the versioned GeoJSON/CSV in `data/processed/`; `site/`
is a generated artefact and is not checked in (see `.gitignore`).

## Automatic deploy (GitHub Actions)

Workflow: `.github/workflows/pages.yml`

- Runs on every push to `main` that changes data (`data/processed/**`) or the
  build script — and on manual trigger (*Actions → Run workflow*).
- Builds the page and deploys it to GitHub Pages.

**One-time activation (manual, cannot be automated):**

1. In the GitHub repo: *Settings → Pages*.
2. Under *Build and deployment → Source* choose **"GitHub Actions"**.
3. On the next push (or manual run) the public URL
   `https://<user>.github.io/<repo>/` appears in the workflow log and under
   *Settings → Pages*.

## Refreshing rail data

Workflow: `.github/workflows/refresh-data.yml`

- Trigger manually (*Actions → "Bahndaten aktualisieren (Overpass)" → Run
  workflow*).
- Fetches fresh data from the Overpass API (`tools/fetch_cfr_data.py`) and opens
  a **pull request** with the data diff (branch `data/overpass-refresh`).
- After review/merge, `pages.yml` rebuilds the site automatically.

> The Overpass API can be slow or temporarily unavailable. The refresh therefore
> runs only on manual trigger (a weekly `cron` is commented out in the workflow
> and can be enabled if needed).
