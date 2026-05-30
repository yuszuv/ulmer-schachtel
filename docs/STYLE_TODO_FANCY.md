# Ulmer Schachtel – TODO: Fancy Style (historical)

## Goal for a later stage

A visually enhanced travel planner with a historical map character, inspired by
late-18th-century cartographic aesthetics.

## Style reference (recorded)

Reference page:
`https://www.vintage-maps.com/de/antike-landkarten/europa/rumaenien-moldawien/von-reilly-rumaenien-moldawien-temescher-banat-temeswar-timisoara::12254`

Key features from the page:

- Map title: "Das Temeschvarer Bannat."
- Cartographer: Franz Johann Joseph von Reilly
- Year: 1791 (Vienna)
- Context: from "Schauplatz der fünf Theile der Welt" (1789–1806)
- Aesthetic: hand-coloured, warm paper tone, fine lettering

## Historical base map: Arcanum Maps (XYZ tiles)

**Arcanum Maps** (maps.arcanum.com) provides the Habsburg military surveys as
an XYZ tile service. The `-transylvania`-specific layers return empty tiles for
Romania — only the `europe-*` layers have actual coverage.

Working layers for Romania (tested):

| Survey | Period | Layer name |
|---|---|---|
| 1st Military Survey | 1763–1790 | `europe-18century-firstsurvey` |
| 2nd Military Survey | 1806–1869 | `europe-19century-secondsurvey` |
| 3rd Military Survey | 1869–1887 | `europe-19century-thirdsurvey` |

Add in QGIS (*Layer → Add Layer → XYZ Tile Layer*):

```
URL:     https://tiles.arcanum.com/mercator/europe-19century-secondsurvey/{z}/{x}/{y}
Referer: https://maps.arcanum.com
Min/Max Zoom: 5 / 14
```

Adjust the layer name for other periods. Place below your own vector layers.

> Chronologically and geographically a perfect match for the style reference
> (von Reilly 1791): the 1st Military Survey was produced in parallel during the
> same decade.

## Visual TODOs

- Prepare the historical base map:
  - Embed Arcanum WMS (see above) instead of a local raster file
  - Optional: cache tiles in `data/reference/historical` for offline QField use
- Colour palette:
  - Parchment background, sepia lines, muted accent colours
- Typography:
  - Serif font for titles/place names, subtle sans-serif for metadata
- Symbology:
  - Differentiated markers for `dracula_city`, `city`, `danube_delta`
- Route visualisation:
  - Historical travel-axis style (dotted/dashed, not modern-neon)
- Map furniture:
  - Scale bar, north arrow, subtle cartouche with travel route

## Functional TODOs for "Fancy"

- Interactive day-by-day itinerary planning
- Weighting slider: Nature / City / History
- Export "daily plan" for QField forms
- Optional web viewer as a second interface alongside QGIS/QField
