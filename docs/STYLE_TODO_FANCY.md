# Ulmer Schachtel – TODO: Fancy Style (historical)

## Goal for a later stage

A visually enhanced travel planner with a historical map character, inspired by
late-18th-century cartographic aesthetics.

## Atlas references for the Fancy stage

The visual design for the Fancy stage draws on two printed atlas traditions as
primary reference:

### 1. Universal Weltatlas — Stuttgarter Hausbücherei, 7th edition, 1952

A popular German general atlas from the immediate postwar period. Cartographic
house style reflects Central European mid-century conventions:

- **Colour palette:** muted, flat — soft terrain washes in yellow-ochre and
  khaki for lowlands, stepwise blue-grey for highlands, no photographic
  hillshading. Colours are kept within a tight, harmonious range; no single
  element dominates.
- **Linework hierarchy:** clear separation between political borders (solid,
  heavier weight), administrative subdivisions (thinner), rivers (blue, tapered
  from source), and coastal lines (finely vignette-shaded on the sea side in
  some plates).
- **Typography:** serifed roman for country and region names, spaced capitals
  for large units, italic for water bodies — a classical tripartite system.
  Label sizes are graded in steps; the progression is legible without being
  mechanical.
- **Legend and map furniture:** compact, self-contained legend panels, scale
  bars without decorative excess. Projection and source noted in a small footer
  typeset in a lighter weight. No cartouche.
- **Density:** moderately high. Small settlements, relief names, and rail lines
  coexist without crowding because of disciplined type sizing and symbol
  differentiation.

Useful as a reference for: colour ramp for the terrain wash, label hierarchy
rules, line weight ratios between border/rail/hydrography.

### 2. Putzger – Historischer Weltatlas — Velhagen & Klasing, 1978 edition

A long-established German historical school atlas, in continuous publication
from the late 19th century with periodic revision. The 1978 edition reflects
West German postwar cartographic standards applied to historical content:

- **Colour palette:** politically coded — empires and territories are coloured
  by polity using a coordinated pastel set. Colours are stable across plates so
  that the same state always reads the same. Background territory is a neutral
  cream/stone; water a quiet, unsaturated blue.
- **Temporal logic:** boundaries are shown as they existed at a specific date,
  clearly labelled. Successor territories are shaded distinctly. This is the
  paradigm to follow when depicting the Habsburg and Ottoman situation ca. 1900.
- **Relief:** schematic hatching or flat tinting — no photographic hillshade.
  Relief is subordinate; political boundaries are primary.
- **Typography:** bold roman upright for empire-level names, spaced for region
  names, italic for rivers and seas. Historical name forms (e.g. *Siebenbürgen*
  rather than *Transylvania*) are standard throughout.
- **Marginal apparatus:** short explanatory text, legend keyed to colours and
  hatch patterns, date range prominently placed. Scale bar calibrated to
  practical units (100 km, 500 miles).

Useful as a reference for: empire-territory colour logic (see
`historische_reiche.geojson`), historical name forms, labelling hierarchy for
political units, treatment of contested/overlapping zones.

### 3. Franz Johann Joseph von Reilly — "Das Temeschvarer Bannat", 1791

Copper engraving, hand-coloured, published in Vienna as part of *Schauplatz der
fünf Theile der Welt* (1789–1806). Source:
`https://www.vintage-maps.com/de/antike-landkarten/europa/rumaenien-moldawien/von-reilly-rumaenien-moldawien-temescher-banat-temeswar-timisoara::12254`

Where the two printed atlases above represent 20th-century rationalised
cartography, von Reilly represents the handcraft tradition that preceded it —
and that directly shaped the aesthetic the Fancy stage aims to evoke:

- **Hand-colouring:** territories are washed with translucent watercolour
  applied by hand over the engraved linework. Colours bleed slightly at edges,
  overlap imperfectly, and vary in intensity — a warmth that flat digital fills
  cannot replicate directly, but can approximate through texture, opacity, and
  carefully chosen hues with slight variation.
- **Copperplate linework:** relief is rendered through fine hachures — short,
  parallel strokes that follow slope direction and increase in density toward
  valley floors. This is the formal ancestor of the schematic hatching in
  Putzger; here it is finer, more laborious, and visually richer. The
  distinction between ridge, slope, and plain reads immediately without any
  colour gradient.
- **Cartouche:** the title is set inside an ornamental cartouche — a framed
  decorative panel, often incorporating rococo flourishes, allegorical figures,
  or stylised natural elements. This is the primary site of typographic display
  in late-18th-century cartography; the map body itself uses restrained lettering.
- **Letterforms:** the engraved script of the 1790s mixes roman upright for
  place names with a flowing chancery italic for rivers and regions. Letter
  spacing is generous; names curve to follow linear features (rivers, roads,
  mountain chains). The ductus — the rhythm and angle of the cut — gives the
  text a warmth absent from typeset letterpress.
- **Warm paper tone:** the cream-to-amber ground of aged laid paper is not
  incidental — it integrates with the hand-colouring and makes the whole image
  read as a unified object. For the Fancy stage, a warm base tint (rather than
  neutral white) is essential to achieve a comparable register.

Useful as a reference for: cartouche design and placement, hachure-style relief
treatment, engraved label ductus (inform font choice and label curvature), warm
paper-tone baseline for the overall colour temperature.

### Design intent

The Fancy stage does not reproduce either atlas literally. The intent is to
work in the *spirit* of this tradition: restrained colour, clear hierarchy,
serif typography, no glows or drop shadows, and a reading experience that
rewards attention. Think of a well-designed 1960s travel map printed on
slightly warm stock — not a pastiche, but something that could have been on
the same shelf.

Concrete decisions to make when implementing:

- Choose a base colour for each political unit in `historische_reiche` that is
  clearly distinct but sits within the Putzger pastel register (consult the
  1978 plates for the Habsburg/Romanian/Ottoman palette).
- Apply the Universal Weltatlas line-weight ratios to rail, river, and border
  layers (rail should be *lighter* than political borders, rivers lighter still
  at source).
- Use only one or two typefaces: a classical roman serif (e.g. EB Garamond,
  Gentium) + optionally a companion italic. Avoid geometric or humanist sans.
- Scale labels in no more than four sizes; label positions should follow the
  classical rules (name runs along the feature, water names italic, terrain
  names spaced roman).

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
