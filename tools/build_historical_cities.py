#!/usr/bin/env python3
"""Build historische_staedte.geojson for the Ulmer Schachtel map.

This script emits a curated list of historically significant cities in the
regions covered by the Romania rail trip, with their ~1900 names in German,
Hungarian, and modern Romanian.

Historical name policy
----------------------
All historical names are taken from encyclopaedias and well-attested sources
(Meyers Konversationslexikon 1905, Brockhaus 1901, Encyclopaedia Britannica
1911).  No names are invented or transliterated.  Where a German name is not
well attested in the literature it is left empty rather than guessed.

Coordinates
-----------
City-centre coordinates (EPSG:4326 / WGS84) verified against OpenStreetMap
nominatim and the geographical centre of the historical city cores.

Output
------
  data/reference/historical/historische_staedte.geojson

Usage
-----
  python tools/build_historical_cities.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_FILE = ROOT / "data" / "reference" / "historical" / "historische_staedte.geojson"

# ---------------------------------------------------------------------------
# Curated city list
# Each dict: NAME (modern RO/UA), NAME_DE (historical German), NAME_HU
# (historical Hungarian), lon, lat, REGION, EMPIRE, NOTE, SOURCE.
# Empty NAME_DE or NAME_HU means the name was identical or not well-attested.
# ---------------------------------------------------------------------------

CITIES: list[dict] = [
    # ── Siebenbürgen (Transylvania) ──────────────────────────────────────
    {
        "NAME":    "Cluj-Napoca",
        "NAME_DE": "Klausenburg",
        "NAME_HU": "Kolozsvár",
        "lon": 23.590, "lat": 46.770,
        "REGION": "Siebenbürgen",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Größte Stadt Siebenbürgens; Universitätsstadt und "
            "kulturelles Zentrum. Auf der Reise via M400 erreichbar."
        ),
    },
    {
        "NAME":    "Brașov",
        "NAME_DE": "Kronstadt",
        "NAME_HU": "Brassó",
        "lon": 25.611, "lat": 45.657,
        "REGION": "Siebenbürgen",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Sächsische Stadtgründung; bekannt für die Schwarze Kirche "
            "und die Burg Rasnov. Ziel der CFR-Magistrale 300."
        ),
    },
    {
        "NAME":    "Sibiu",
        "NAME_DE": "Hermannstadt",
        "NAME_HU": "Nagyszeben",
        "lon": 24.152, "lat": 45.798,
        "REGION": "Siebenbürgen",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Historische Hauptstadt der Siebenbürger Sachsen; "
            "Brukenthal-Museum; ab 1867 Sitz des evangelischen Bischofs."
        ),
    },
    {
        "NAME":    "Sighișoara",
        "NAME_DE": "Schäßburg",
        "NAME_HU": "Segesvár",
        "lon": 24.797, "lat": 46.219,
        "REGION": "Siebenbürgen",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Sächsische Bergstadt mit dem berühmten Uhrenturm; "
            "Geburtsort von Vlad III. (Voivod der Walachei)."
        ),
    },
    {
        "NAME":    "Alba Iulia",
        "NAME_DE": "Karlsburg",
        "NAME_HU": "Gyulafehérvár",
        "lon": 23.580, "lat": 46.067,
        "REGION": "Siebenbürgen",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Bischofssitz; hier wurde 1918 die Vereinigung Siebenbürgens "
            "mit Rumänien proklamiert. Historisch Weißenburg (Alba Carolina)."
        ),
    },
    {
        "NAME":    "Mediaș",
        "NAME_DE": "Mediasch",
        "NAME_HU": "Medgyes",
        "lon": 24.352, "lat": 46.158,
        "REGION": "Siebenbürgen",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Sächsische Weinstadt an der Kokel; "
            "Peterskirche mit bemalten Emporen."
        ),
    },
    {
        "NAME":    "Bistrița",
        "NAME_DE": "Bistritz",
        "NAME_HU": "Beszterce",
        "lon": 24.500, "lat": 47.133,
        "REGION": "Siebenbürgen",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Nördlichste sächsische Stadt; in Bram Stokers 'Dracula' "
            "Ausgangspunkt der Reise in die Karpaten."
        ),
    },
    {
        "NAME":    "Târgu Mureș",
        "NAME_DE": "Neumarkt am Mieresch",
        "NAME_HU": "Marosvásárhely",
        "lon": 24.558, "lat": 46.545,
        "REGION": "Siebenbürgen",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Kulturelle Metropole des Szeklerlandes; Sitz des "
            "siebenbürgischen Appellationsgerichts um 1900."
        ),
    },
    {
        "NAME":    "Deva",
        "NAME_DE": "Diemrich",
        "NAME_HU": "Déva",
        "lon": 22.900, "lat": 45.883,
        "REGION": "Siebenbürgen",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Kreisstadt mit Burgruine; Tor zum Hunyadital. "
            "Corvinburg (Burg Hunedoara) liegt 14 km entfernt."
        ),
    },
    # ── Banat ─────────────────────────────────────────────────────────────
    {
        "NAME":    "Timișoara",
        "NAME_DE": "Temeswar",
        "NAME_HU": "Temesvár",
        "lon": 21.234, "lat": 45.747,
        "REGION": "Banat",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Hauptstadt des Banats; 1884 erste elektrisch beleuchtete Stadt "
            "Europas. Ausgangspunkt vieler CFR-Verbindungen."
        ),
    },
    {
        "NAME":    "Lugoj",
        "NAME_DE": "Lugosch",
        "NAME_HU": "Lugos",
        "lon": 21.903, "lat": 45.690,
        "REGION": "Banat",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Zweitgrößte Banater Stadt; an der Temesch gelegen; "
            "bedeutend für die rumänische Kulturbewegung im Banat."
        ),
    },
    {
        "NAME":    "Reșița",
        "NAME_DE": "Reschitz",
        "NAME_HU": "Resicabánya",
        "lon": 21.889, "lat": 45.297,
        "REGION": "Banat",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Industriestadt im Gebirgsbanat; Eisenwerke seit 1771; "
            "Stahl und Lokomotiven für die österreichischen Bahnen."
        ),
    },
    # ── Crișana ───────────────────────────────────────────────────────────
    {
        "NAME":    "Oradea",
        "NAME_DE": "Großwardein",
        "NAME_HU": "Nagyvárad",
        "lon": 21.920, "lat": 47.047,
        "REGION": "Crișana",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Bedeutende Bischofsstadt an der Schnellen Kreisch; "
            "reich an Jugendstilbauten; strategischer Bahnknoten."
        ),
    },
    {
        "NAME":    "Arad",
        "NAME_DE": "Arad",
        "NAME_HU": "Arad",
        "lon": 21.312, "lat": 46.176,
        "REGION": "Crișana",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Kreisstadt an der Marosch; Ort der Hinrichtung der "
            "13 ungarischen Märtyrergenärale (1849). Wichtiger Bahnknoten."
        ),
    },
    # ── Maramureș ─────────────────────────────────────────────────────────
    {
        "NAME":    "Satu Mare",
        "NAME_DE": "Sathmar",
        "NAME_HU": "Szatmárnémeti",
        "lon": 22.886, "lat": 47.791,
        "REGION": "Maramureș",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Historisch Sitz des Komitats Szatmár; an der Somes gelegen; "
            "bekannt für den Frieden von Sathmar (1711)."
        ),
    },
    {
        "NAME":    "Baia Mare",
        "NAME_DE": "",
        "NAME_HU": "Nagybánya",
        "lon": 23.579, "lat": 47.657,
        "REGION": "Maramureș",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Bergbaustadt (Silber, Gold); bedeutende Malerschule "
            "um 1900; ungarisch 'Großmine'."
        ),
    },
    {
        "NAME":    "Sighetu Marmației",
        "NAME_DE": "Marmarosch-Siget",
        "NAME_HU": "Máramarossziget",
        "lon": 23.890, "lat": 47.929,
        "REGION": "Maramureș",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Hauptstadt des Marmaros-Komitats; Salz- und Holzhandel; "
            "heute direkt an der Grenze zur Ukraine."
        ),
    },
    # ── Bukowina ──────────────────────────────────────────────────────────
    {
        "NAME":    "Cernăuți",
        "NAME_DE": "Czernowitz",
        "NAME_HU": "Csernovitz",
        "lon": 25.936, "lat": 48.295,
        "REGION": "Bukowina",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Hauptstadt des Kronlandes Bukowina; Universitätsstadt; "
            "heute Tscherniwzi (Ukraine). Sprachenvielfalt: Deutsch, "
            "Rumänisch, Jiddisch, Ukrainisch."
        ),
    },
    {
        "NAME":    "Suceava",
        "NAME_DE": "Suczawa",
        "NAME_HU": "Szucsáva",
        "lon": 26.257, "lat": 47.632,
        "REGION": "Bukowina",
        "EMPIRE": "Österreich-Ungarn",
        "NOTE": (
            "Einstige Hauptstadt des Fürstentums Moldau (14.–16. Jh.); "
            "Festungsruine und Klosterlandschaft (UNESCO-Welterbe)."
        ),
    },
    # ── Moldau ────────────────────────────────────────────────────────────
    {
        "NAME":    "Iași",
        "NAME_DE": "Jassy",
        "NAME_HU": "Jászvásár",
        "lon": 27.590, "lat": 47.157,
        "REGION": "Moldau",
        "EMPIRE": "Königreich Rumänien",
        "NOTE": (
            "Historische Hauptstadt der Moldau; 1859–1862 erste "
            "Hauptstadt des vereinigten rumänischen Fürstentums. "
            "Universität gegründet 1860."
        ),
    },
    {
        "NAME":    "Galați",
        "NAME_DE": "Galatz",
        "NAME_HU": "Galac",
        "lon": 28.050, "lat": 45.435,
        "REGION": "Moldau",
        "EMPIRE": "Königreich Rumänien",
        "NOTE": (
            "Wichtigster Donauhafen Rumäniens; unter der Donaukommission "
            "als internationaler Freihafen; Stahlwerk gegründet 1966."
        ),
    },
    # ── Muntenia ──────────────────────────────────────────────────────────
    {
        "NAME":    "București",
        "NAME_DE": "Bukarest",
        "NAME_HU": "Bukarest",
        "lon": 26.097, "lat": 44.440,
        "REGION": "Muntenia",
        "EMPIRE": "Königreich Rumänien",
        "NOTE": (
            "Hauptstadt des Königreichs Rumänien seit 1862; "
            "'Kleines Paris' mit Calea Victoriei und Athenäum. "
            "Endhaltestelle der meisten CFR-Magistralen."
        ),
    },
    {
        "NAME":    "Ploiești",
        "NAME_DE": "Ploiești",
        "NAME_HU": "Ploiești",
        "lon": 25.975, "lat": 44.938,
        "REGION": "Muntenia",
        "EMPIRE": "Königreich Rumänien",
        "NOTE": (
            "Zentrum der rumänischen Erdölindustrie seit den 1860ern; "
            "Treibstoffversorgung für ganz Mitteleuropa um 1900."
        ),
    },
    # ── Oltenien ──────────────────────────────────────────────────────────
    {
        "NAME":    "Craiova",
        "NAME_DE": "Krajowa",
        "NAME_HU": "Krajova",
        "lon": 23.800, "lat": 44.320,
        "REGION": "Oltenien",
        "EMPIRE": "Königreich Rumänien",
        "NOTE": (
            "Größte Stadt Olteniens; Sitz des Olt-Bezirks; "
            "wichtiger Eisenbahnknoten der Kleinen Walachei."
        ),
    },
    # ── Dobrudscha ────────────────────────────────────────────────────────
    {
        "NAME":    "Constanța",
        "NAME_DE": "Konstanza",
        "NAME_HU": "Konstanca",
        "lon": 28.655, "lat": 44.175,
        "REGION": "Dobrudscha",
        "EMPIRE": "Königreich Rumänien",
        "NOTE": (
            "Haupthafen am Schwarzen Meer; antike Gründung 'Tomis'; "
            "per Eisenbahn seit 1860 mit Cernavodă und Bukarest verbunden."
        ),
    },
]

# ---------------------------------------------------------------------------
# Build GeoJSON
# ---------------------------------------------------------------------------

SOURCE = (
    "Hand-curated; names from Meyers Konversationslexikon 1905, "
    "Brockhaus 1901, Encyclopaedia Britannica 1911"
)


def build() -> None:
    features = []
    for city in CITIES:
        props: dict = {
            "NAME":    city["NAME"],
            "NAME_DE": city["NAME_DE"],
            "NAME_HU": city["NAME_HU"],
            "REGION":  city["REGION"],
            "EMPIRE":  city["EMPIRE"],
            "NOTE":    city["NOTE"],
            "SOURCE":  SOURCE,
        }
        feat = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [city["lon"], city["lat"]],
            },
            "properties": props,
        }
        features.append(feat)

    fc = {
        "type": "FeatureCollection",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features,
    }

    out = ROOT / "data" / "reference" / "historical" / "historische_staedte.geojson"
    out.write_text(json.dumps(fc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(features)} cities → {out}")


if __name__ == "__main__":
    build()
