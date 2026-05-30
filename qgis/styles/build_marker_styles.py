#!/usr/bin/env python3
"""Build marker QML styles with embedded SVG icons.

Was macht dieses Skript?
------------------------
QGIS speichert Layer-Symbologie in ``.qml``-Dateien (XML-Format). Zwei unserer
Layer (``poi_destinations``, ``rail_stations``) nutzen SVG-Icons als Marker.
Statt den SVG-Pfad in die QML zu schreiben (was auf dem Handy (QField) brechen
würde, weil die Icons dort nicht liegen), werden die SVGs per Base64 *direkt in
die QML eingebettet* — die Datei wird damit völlig self-contained und
pfadunabhängig.

Wann ausführen?
---------------
Nach jeder Änderung an den SVG-Dateien unter ``qgis/styles/icons/``::

    python qgis/styles/build_marker_styles.py

Die erzeugten QML-Dateien danach in QGIS per **Load Style → All Categories**
neu laden und das Projekt speichern — erst beim Speichern werden die Styles
ins ``.qgz`` eingebettet (und reisen damit automatisch nach QField).

WICHTIG – „All Categories"-Falle
---------------------------------
Beim Laden eines QML in QGIS gibt es eine Dropdown-Box. Wenn du dort nur
„Symbology" wählst, werden Beschriftungen (Labeling) und Map Tips **nicht**
geladen, auch wenn sie in der QML vorhanden sind. Immer **„All Categories"**
wählen.

Map Tips
--------
Map Tips sind HTML-Karten, die in QGIS und QField erscheinen, wenn man ein
Feature antippt (Identify). Inhalt: Name, Kategorie, Priorität, Notizen (POI)
bzw. Name + Stadt (Bahnhof). Der HTML darf QGIS-Ausdrücke in der Form
``[% "feldname" %]`` enthalten — QGIS ersetzt sie beim Anzeigen durch den
tatsächlichen Attributwert.
"""

from __future__ import annotations

import base64
from pathlib import Path

HERE = Path(__file__).resolve().parent
ICONS = HERE / "icons"


# ---------------------------------------------------------------------------
# Hilfsfunktionen – XML-Bausteine
# ---------------------------------------------------------------------------

def b64(svg: str) -> str:
    """SVG-Datei aus icons/ lesen und Base64-kodiert zurückgeben."""
    return base64.b64encode((ICONS / svg).read_bytes()).decode("ascii")


def svg_marker(b64data: str, size: float) -> str:
    """Einen QGIS SvgMarker-Layer als XML-Snippet erzeugen.

    ``name=base64:…`` ist die QGIS-Syntax um SVG-Daten direkt einzubetten
    statt eines Dateipfads. Das macht den Style von lokalen Pfaden unabhängig
    — wichtig für QField-Sync, wo die Icons-Ordnerstruktur des Desktops nicht
    existiert.

    Größen-Hinweise:
    - ``size_unit="MM"`` → Millimeter, unabhängig von Bildschirmauflösung.
    - ``scale_method="diameter"`` → die Größe ist der Durchmesser.
    - ``vertical/horizontal_anchor_point="1"`` → Marker am Mittelpunkt
      verankert (0 = oben/links, 1 = Mitte, 2 = unten/rechts).
    """
    return f"""        <!-- SvgMarker: SVG-Icon als Marker, Base64-direkt eingebettet — kein Dateipfad,
             daher in QField ohne lokale Ordnerstruktur verwendbar.
             name="base64:…" = SVG-Inhalt als Data-URI statt Pfadangabe.
             size_unit="MM" = gerätunabhängige Millimeter (nicht Pixel).
             scale_method="diameter" = Größe ist der Durchmesser, nicht der Radius.
             anchor_point="1" = Marker-Mittelpunkt als Ankerpunkt
               (0 = oben/links, 1 = Mitte, 2 = unten/rechts). -->
        <layer class="SvgMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="base64:{b64data}"/>
            <Option name="size" type="QString" value="{size}"/>
            <Option name="size_unit" type="QString" value="MM"/>
            <Option name="angle" type="QString" value="0"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="fixedAspectRatio" type="QString" value="0"/>
            <Option name="scale_method" type="QString" value="diameter"/>
            <Option name="vertical_anchor_point" type="QString" value="1"/>
            <Option name="horizontal_anchor_point" type="QString" value="1"/>
          </Option>
        </layer>"""


def labeling(font_size: float, weight: int, color: str, dist: float) -> str:
    """Beschriftungs-Block für Punkt-Layer erzeugen.

    Parameter:
    - ``weight``: Schriftgewicht (50 ≈ Regular, 75 ≈ Bold in QGIS-Einheiten).
    - ``dist``: Abstand Label→Marker in MM.
    - Buffer (``bufferDraw="1"``): weißer, leicht transparenter Hintergrund
      hinter dem Text — verbessert Lesbarkeit auf bunten Kacheln erheblich.
    - ``predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR"``: QGIS sucht
      automatisch die beste Label-Position (oben rechts zuerst), die andere
      Labels nicht überlappt.
    - ``placement="0"``: „Around Point" — Standard für Punkt-Layer.
    """
    style = "Bold" if weight >= 75 else "Regular"
    return f"""  <!-- Beschriftung: Feld "name", Sans-Serif, mit weißem Hintergrund-Puffer.
       placement="0" = Around Point — QGIS sucht die beste Position rund um den Marker
         (für Linien wäre placement="3" = Curved).
       predefinedPositionOrder = Reihenfolge der geprüften Positionen: oben-rechts
         zuerst (TR), dann TL, BR, BL usw. — QGIS nimmt die erste überlappungsfreie.
       bufferDraw="1" + bufferColor "…,235" = leicht transparenter weißer Puffer
         hinter dem Text → Lesbarkeit auf bunten Kacheln deutlich besser.
       displayAll="0" = Labels werden unterdrückt wenn sie andere überdecken würden
         (Ausnahme info_markers: dort ist displayAll="1", weil es nur einen gibt). -->
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fieldName="name" isExpression="0"
                  fontFamily="Sans Serif" fontSize="{font_size}" fontSizeUnit="Point"
                  fontWeight="{weight}" namedStyle="{style}" fontItalic="0"
                  fontUnderline="0" fontStrikeout="0" fontKerning="1"
                  fontLetterSpacing="0" fontWordSpacing="0"
                  textColor="{color}" textOpacity="1" blendMode="0"
                  multilineHeight="1" multilineHeightUnit="Percentage"
                  textOrientation="horizontal" capitalization="0"
                  allowHtml="0" useSubstitutions="0"
                  previewBkgrdColor="255,255,255,255" legendString="Aa"
                  fontSizeMapUnitScale="3x:0,0,0,0,0,0">
        <text-buffer bufferDraw="1" bufferSize="0.8" bufferSizeUnits="MM"
                     bufferColor="255,255,255,235" bufferOpacity="1"
                     bufferJoinStyle="64" bufferNoFill="0" bufferBlendMode="0"/>
      </text-style>
      <text-format wrapChar="" autoWrapLength="0" useMaxLineLengthForAutoWrap="1"
                   multilineAlign="3" addDirectionSymbol="0"
                   leftDirectionSymbol="&lt;" rightDirectionSymbol=">"
                   reverseDirectionSymbol="0" placeDirectionSymbol="0"
                   formatNumbers="0" decimals="3" plusSign="0"/>
      <placement placement="0" dist="{dist}" distUnits="MM"
                 distMapUnitScale="3x:0,0,0,0,0,0"
                 quadOffset="4" offsetType="0" xOffset="0" yOffset="0"
                 offsetUnits="MM" xOffsetMapUnitScale="3x:0,0,0,0,0,0"
                 yOffsetMapUnitScale="3x:0,0,0,0,0,0"
                 labelOffsetMapUnitScale="3x:0,0,0,0,0,0"
                 rotationAngle="0" rotationUnit="AngleDegrees" priority="5"
                 repeatDistance="0" repeatDistanceUnit="MM"
                 repeatDistanceMapUnitScale="3x:0,0,0,0,0,0"
                 maxCurvedCharAngleIn="25" maxCurvedCharAngleOut="-25"
                 predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR"
                 fitInPolygonOnly="0" centroidWhole="0" centroidInside="0"
                 pointOnSurface="0" pointOnAllParts="0"
                 geometryGeneratorEnabled="0" geometryGeneratorType="PointGeometry"
                 geometryGenerator="" layerType="PointGeometry"
                 overrunDistance="0" overrunDistanceUnit="MM"
                 overrunDistanceMapUnitScale="3x:0,0,0,0,0,0"
                 lineAnchorPercent="0.5" lineAnchorType="0" lineAnchorClipping="0"
                 polygonPlacementFlags="2" allowDegraded="0"
                 mLineDistance="0" mLineDistanceUnit="MM"
                 mLineDistanceMapUnitScale="3x:0,0,0,0,0,0"/>
      <rendering drawLabels="1" displayAll="0" limitNumLabels="0"
                 maxNumLabels="2000" minFeatureSize="0"
                 fontLimitPixelSize="0" fontMinPixelSize="3" fontMaxPixelSize="10000"
                 scaleVisibility="0" scaleMin="1" scaleMax="10000000"
                 obstacle="1" obstacleFactor="1" obstacleType="0"
                 zIndex="0" labelPerPart="0" mergeLines="0" upsidedownLabels="0"/>
      <dd_properties>
        <Option type="Map">
          <Option name="name" type="QString" value=""/>
          <Option name="properties"/>
          <Option name="type" type="QString" value="collection"/>
        </Option>
      </dd_properties>
    </settings>
  </labeling>"""


def map_tip(html: str) -> str:
    """Map-Tip-Block erzeugen.

    Map Tips sind HTML-Karten, die in QGIS/QField beim Antippen eines Features
    erscheinen. ``[% "feldname" %]`` in HTML ist QGIS-Expression-Syntax und
    wird durch den tatsächlichen Attributwert ersetzt.

    Stil: Serif-Schrift, Sepia-Töne, schmal (max-width 260px → passt aufs Handy).
    Orientiert sich an ``info_markers.qml`` für visuelle Konsistenz.

    WICHTIG: Map Tips müssen mit „Load Style → All Categories" geladen werden,
    sonst werden sie still ignoriert.
    """
    return (
        "  <!-- Map Tip: HTML-Karte beim Antippen in QGIS / QField (Identify / Finger-Tap).\n"
        "       CDATA schützt HTML-Sonderzeichen (<, >, &) vor XML-Interpretation.\n"
        "       [% \"feldname\" %] = QGIS-Expression → wird beim Anzeigen durch den\n"
        "         tatsächlichen Attributwert ersetzt (z.B. [% \"name\" %] → \"Brașov\").\n"
        "       WICHTIG: nur aktiv wenn Style mit \"All Categories\" geladen wurde. -->\n"
        f"  <mapTip><![CDATA[{html}]]></mapTip>"
    )


# ---------------------------------------------------------------------------
# Style-Funktionen – ein Aufruf pro Layer
# ---------------------------------------------------------------------------

def build_poi() -> str:
    """QML für den ``poi_destinations``-Layer erzeugen.

    Renderer-Typ: ``categorizedSymbol`` — jede Kategorie bekommt ein eigenes
    Symbol. Die Kategorien entsprechen dem Attribut ``category`` im GeoJSON:
    - ``dracula_city``  → dunkles Kreissymbol (poi_dracula.svg)
    - ``city``          → Quadrat in Sepiabraun (poi_city.svg)
    - ``danube_delta``  → Dreieck in gedämpftem Türkis (poi_delta.svg)

    Warum ``categorizedSymbol`` statt ``singleSymbol``?
    Mit ``categorizedSymbol`` wählt QGIS automatisch das richtige Icon anhand
    des Attributwerts — kein manuelles Zuweisen nötig.

    Map Tip: Name (fett, sepia), Kategorie + Priorität (klein, grau), Notizen.
    """
    # Schlüssel = interne Symbol-ID; Wert = (Kategoriewert, Legendenname, SVG-Datei, Größe in MM)
    icons = {
        "0": ("dracula_city", "Dracula-Stadt", b64("poi_dracula.svg"), 7.5),
        "1": ("city", "Stadt", b64("poi_city.svg"), 7.0),
        "2": ("danube_delta", "Donaudelta", b64("poi_delta.svg"), 7.0),
    }

    # <categories>: verknüpft jeden Attributwert mit der Symbol-ID
    categories = "\n".join(
        f'      <category value="{val}" label="{label}" symbol="{sid}" render="true"/>'
        for sid, (val, label, _, _) in icons.items()
    )

    # <symbols>: die eigentlichen Marker-Definitionen (SVG base64-eingebettet)
    symbols = "\n".join(
        f'      <symbol name="{sid}" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">\n'
        f"{svg_marker(data, size)}\n      </symbol>"
        for sid, (_, _, data, size) in icons.items()
    )

    # Map Tip: [% "feldname" %] wird beim Antippen durch den Attributwert ersetzt
    tip_html = (
        '<div style="font-family:serif;color:#39312b;max-width:260px">'
        '<div style="font-size:14px;font-weight:bold;color:#6b4f2a">[% "name" %]</div>'
        '<div style="font-size:11px;color:#888;margin-top:2px">'
        '[% "category" %]&nbsp;·&nbsp;Prio&nbsp;[% "priority" %]'
        '</div>'
        '<div style="font-size:12px;margin-top:6px">[% "notes" %]</div>'
        '</div>'
    )

    return f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Style für: poi_destinations (Punkt-Layer)
  Generiert von: qgis/styles/build_marker_styles.py
  Nicht manuell bearbeiten — Änderungen werden beim nächsten Generieren
  überschrieben. Stattdessen build_marker_styles.py anpassen, dann neu ausführen.
-->
<qgis version="3.34.0" styleCategories="Symbology|Labeling|MapTips">
  <!-- Renderer: categorizedSymbol — jede POI-Kategorie bekommt ein eigenes Icon.
       attr="category" = QGIS wählt das Symbol anhand dieses GeoJSON-Attributfelds.
       Mögliche Werte (value=): dracula_city, city, danube_delta.
       Im Unterschied zu singleSymbol (gleicher Marker für alle) erlaubt dieser
       Typ, pro Kategorie Farbe, Form und Größe individuell zu steuern. -->
  <renderer-v2 attr="category" type="categorizedSymbol" symbollevels="0">
    <categories>
{categories}
    </categories>
    <symbols>
{symbols}
    </symbols>
    <source-symbol>
      <symbol name="0" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
{svg_marker(icons['0'][2], 7.0)}
      </symbol>
    </source-symbol>
  </renderer-v2>
{labeling(8, 75, "107,79,42,255", 1.5)}
{map_tip(tip_html)}
</qgis>
"""


def build_stations() -> str:
    """QML für den ``rail_stations``-Layer erzeugen.

    Renderer-Typ: ``singleSymbol`` — alle Bahnhöfe sehen gleich aus. Kein
    Kategorisieren nötig, da es keine Untertypen gibt.

    Labeling: kleinere Schrift (6.5pt, grau-blau) als bei POIs (8pt, sepia) —
    Bahnhöfe sind sekundäre Information und sollen die POI-Namen nicht
    überdecken.

    Map Tip: Bahnhofsname (fett, dunkelgrau) + Stadt (klein, grau).
    """
    data = b64("rail_station.svg")

    tip_html = (
        '<div style="font-family:serif;color:#39312b;max-width:260px">'
        '<div style="font-size:14px;font-weight:bold;color:#4c4c4c">[% "name" %]</div>'
        '<div style="font-size:11px;color:#888;margin-top:2px">[% "city" %]</div>'
        '</div>'
    )

    return f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Style für: rail_stations (Punkt-Layer)
  Generiert von: qgis/styles/build_marker_styles.py
  Nicht manuell bearbeiten — Änderungen werden beim nächsten Generieren
  überschrieben. Stattdessen build_marker_styles.py anpassen, dann neu ausführen.
-->
<qgis version="3.34.0" styleCategories="Symbology|Labeling|MapTips">
  <!-- Renderer: singleSymbol — alle Bahnhöfe sehen gleich aus, keine Untertypen.
       Im Unterschied zu categorizedSymbol (POIs) gibt es hier nur ein Symbol
       für alle Features. alpha="1" = vollständig opak. -->
  <renderer-v2 type="singleSymbol" symbollevels="0">
    <symbols>
      <symbol name="0" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
{svg_marker(data, 5.5)}
      </symbol>
    </symbols>
  </renderer-v2>
{labeling(6.5, 50, "52,73,94,255", 1.0)}
{map_tip(tip_html)}
</qgis>
"""


def main() -> None:
    (HERE / "poi_destinations.qml").write_text(build_poi(), encoding="utf-8")
    (HERE / "rail_stations.qml").write_text(build_stations(), encoding="utf-8")
    print("✓  poi_destinations.qml  (Symbology + Labeling + MapTips)")
    print("✓  rail_stations.qml     (Symbology + Labeling + MapTips)")
    print()
    print("Nächster Schritt in QGIS:")
    print("  Layer Properties → Style → Load Style → All Categories auswählen")
    print("  → Projekt speichern  (erst dann sind Styles + Map Tips im .qgz eingebettet)")


if __name__ == "__main__":
    main()
