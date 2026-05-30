"""CFR magistrală definitions — static, hand-curated domain data.

This module is pure data: no IO, no network, no side effects.  It contains
the canonical list of Romania's CFR main lines (M200–M900) with their stops
and OSM name aliases used during ingest.

Why a separate module?
  The definitions are domain knowledge, not configuration.  Separating them
  from the ingest logic (overpass.py / ingest.py) makes both easier to read:
  here you can see the network at a glance; there you see the algorithm.

Known OSM name deviations (maintained as aliases):
  "Gara de Nord"    → București Nord
  "Gara Iași"       → Iași
  "Cluj Napoca"     → Cluj-Napoca  (OSM omits the hyphen)
  "Drobeta Turnu Severin" → Drobeta-Turnu Severin
"""

from .domain import Magistrale, Stop

MAIN_LINES: tuple[Magistrale, ...] = (
    Magistrale(
        ref="M200",
        route_name="M200 · Brașov – Sibiu – Arad (Karpatenrand)",
        tags="hauptstrecke,siebenbürgen,karpaten",
        length_km=500,
        stops=(
            Stop("Brașov", "Brașov"),
            Stop("Făgăraș", "Făgăraș"),
            Stop("Sibiu", "Sibiu"),
            Stop("Simeria", "Simeria"),
            Stop("Deva", "Deva"),
            Stop("Arad", "Arad"),
            Stop("Curtici", "Curtici"),
        ),
    ),
    Magistrale(
        ref="M300",
        route_name="M300 · București – Brașov – Cluj-Napoca – Oradea (Transsilvanien-Magistrale)",
        tags="hauptstrecke,siebenbürgen,dracula,city",
        length_km=647,
        stops=(
            Stop("București Nord", "București", ("Gara de Nord",)),
            Stop("Ploiești Vest", "Ploiești"),
            Stop("Brașov", "Brașov"),
            Stop("Sighișoara", "Sighișoara"),
            Stop("Mediaș", "Mediaș"),
            Stop("Teiuș", "Teiuș"),
            Stop("Cluj-Napoca", "Cluj-Napoca", ("Cluj Napoca",)),
            Stop("Oradea", "Oradea"),
        ),
    ),
    Magistrale(
        ref="M400",
        route_name="M400 · Brașov – Dej – Satu Mare (Nordsiebenbürgen)",
        tags="hauptstrecke,maramuresch,nord",
        length_km=560,
        stops=(
            Stop("Brașov", "Brașov"),
            Stop("Dej Călători", "Dej"),
            Stop("Baia Mare", "Baia Mare"),
            Stop("Satu Mare", "Satu Mare"),
        ),
    ),
    Magistrale(
        ref="M500",
        route_name="M500 · București – Bacău – Suceava (Moldau-Magistrale)",
        tags="hauptstrecke,moldau,city",
        length_km=488,
        stops=(
            Stop("București Nord", "București", ("Gara de Nord",)),
            Stop("Ploiești Vest", "Ploiești"),
            Stop("Buzău", "Buzău"),
            Stop("Focșani", "Focșani"),
            Stop("Bacău", "Bacău"),
            Stop("Pașcani", "Pașcani"),
            Stop("Suceava", "Suceava"),
        ),
    ),
    Magistrale(
        ref="M600",
        route_name="M600 · Făurei – Bârlad – Iași (Ost-Moldau)",
        tags="hauptstrecke,moldau,ost",
        length_km=395,
        stops=(
            Stop("Făurei", "Făurei"),
            Stop("Bârlad", "Bârlad"),
            Stop("Vaslui", "Vaslui"),
            Stop("Iași", "Iași", ("Gara Iași",)),
        ),
    ),
    Magistrale(
        ref="M700",
        route_name="M700 · București – Brăila – Galați (Donau-Anschluss)",
        tags="hauptstrecke,donau,galați",
        length_km=229,
        stops=(
            Stop("București Nord", "București", ("Gara de Nord",)),
            Stop("Buzău", "Buzău"),
            Stop("Făurei", "Făurei"),
            Stop("Brăila", "Brăila"),
            Stop("Galați", "Galați"),
        ),
    ),
    Magistrale(
        ref="M800",
        route_name="M800 · București – Constanța – Mangalia (Schwarzmeer-Küste)",
        tags="hauptstrecke,küste,schwarzmeer,delta",
        length_km=225,
        stops=(
            Stop("București Nord", "București", ("Gara de Nord",)),
            Stop("Fetești", "Fetești"),
            Stop("Medgidia", "Medgidia"),
            Stop("Constanța", "Constanța"),
            Stop("Mangalia", "Mangalia"),
        ),
    ),
    Magistrale(
        ref="M900",
        route_name="M900 · București – Craiova – Timișoara (Banat-Magistrale)",
        tags="hauptstrecke,banat,donau,city",
        length_km=533,
        stops=(
            Stop("București Nord", "București", ("Gara de Nord",)),
            Stop("Craiova", "Craiova"),
            Stop("Drobeta-Turnu Severin", "Drobeta-Turnu Severin",
                 ("Drobeta Turnu Severin",)),
            Stop("Caransebeș", "Caransebeș"),
            Stop("Timișoara Nord", "Timișoara"),
        ),
    ),
)
