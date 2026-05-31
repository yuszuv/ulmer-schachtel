"""Historical regions of Romania mapped to their ISO 3166-2 county codes.

Used by the WikiVoyage city fetch (``wikivoyage.py``) to build one Overpass
request per historical region and tag each city with its region name.  The
spatial join ("which city belongs to which region") is handled entirely inside
Overpass via the ``ISO3166-2`` county areas — no shapely / point-in-polygon
needed (the project is deliberately stdlib-only).

County assignment
-----------------
The mapping follows de.Wikipedia "Liste der historischen Regionen in Rumänien
und der Republik Moldau" and de.wikivoyage "Kreischgebiet", verified 2026-05-31.

Each county is assigned to exactly one region.  Border counties with ambiguous
historical membership are assigned to the most common / tourist-facing
classification; the decision is documented inline:

* ``RO-AR`` (Arad): historically split — south of the Mureș = Banat, north-west
  = Crișana/Kreischgebiet. Assigned here to **Kreischgebiet** (Partium sphere).
* ``RO-SJ`` (Sălaj): "largely Kreischgebiet/Partium" per de.wikivoyage;
  occasionally also grouped with Siebenbürgen. Assigned to **Kreischgebiet**.
* ``RO-MH`` (Mehedinți): western tip historically Banat, majority Oltenia.
  Assigned to **Walachei (Oltenia)**.
* ``RO-SV`` (Suceava): southern half = Bukovina, remainder historically Moldau.
  Assigned to **Bukowina** (Suceava city and the painted monasteries are there).
* ``RO-SM`` + ``RO-MM`` combined into **Sathmar/Marmarosch** — avoids splitting
  a single county across two regions.

The region keys are also the ``region`` attribute values in the GeoJSON output
and the legend labels in the QGIS style (``build_marker_styles.py``).
"""

from __future__ import annotations

# region → ISO-3166-2:RO county codes. Every county appears exactly once
# (42 = 41 județe + Municipiul București ``RO-B``).
# Key order = rough west-to-east, also used as legend order in the QGIS style.
HISTORICAL_REGIONS: dict[str, tuple[str, ...]] = {
    "Banat":                ("RO-TM", "RO-CS"),
    "Kreischgebiet":        ("RO-BH", "RO-AR", "RO-SJ"),
    "Sathmar/Marmarosch":   ("RO-SM", "RO-MM"),
    "Siebenbürgen":         ("RO-CJ", "RO-AB", "RO-SB", "RO-BV", "RO-MS",
                             "RO-BN", "RO-CV", "RO-HR", "RO-HD"),
    "Walachei (Muntenia)":  ("RO-AG", "RO-PH", "RO-DB", "RO-IL", "RO-CL",
                             "RO-GR", "RO-TR", "RO-IF", "RO-BZ", "RO-BR", "RO-B"),
    "Walachei (Oltenia)":   ("RO-DJ", "RO-GJ", "RO-MH", "RO-OT", "RO-VL"),
    "Moldau":               ("RO-IS", "RO-BC", "RO-BT", "RO-NT", "RO-VS",
                             "RO-VN", "RO-GL"),
    "Bukowina":             ("RO-SV",),
    "Dobrudscha":           ("RO-CT", "RO-TL"),
}

# Reverse index: county code → region name.  Derived from HISTORICAL_REGIONS so
# there is a single source of truth.
COUNTY_TO_REGION: dict[str, str] = {
    code: region
    for region, codes in HISTORICAL_REGIONS.items()
    for code in codes
}
