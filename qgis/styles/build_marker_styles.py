#!/usr/bin/env python3
"""Baut die Marker-QML-Styles mit eingebetteten SVG-Icons.

Die SVG-Quellen liegen unter ``qgis/styles/icons/`` und werden base64-codiert
direkt in die QML eingebettet (``name=base64:…``). Dadurch sind die Styles
selbst-enthalten und syncen ohne Pfad-/Asset-Probleme nach QField.

Aufruf (nach Änderungen an den SVGs):
    python qgis/styles/build_marker_styles.py
"""

from __future__ import annotations

import base64
from pathlib import Path

HERE = Path(__file__).resolve().parent
ICONS = HERE / "icons"


def b64(svg: str) -> str:
    return base64.b64encode((ICONS / svg).read_bytes()).decode("ascii")


def svg_marker(b64data: str, size: float) -> str:
    return f"""        <layer class="SvgMarker" enabled="1" pass="0" locked="0">
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


# Labeling-Block: fett, mit dezentem weißem Puffer für Lesbarkeit auf Karten.
def labeling(font_size: float, weight: int, color: str, dist: float) -> str:
    style = "Bold" if weight >= 75 else "Regular"
    return f"""  <labeling type="simple">
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


def build_poi() -> str:
    icons = {
        "0": ("dracula_city", "Dracula-Stadt", b64("poi_dracula.svg"), 7.5),
        "1": ("city", "Stadt", b64("poi_city.svg"), 7.0),
        "2": ("danube_delta", "Donaudelta", b64("poi_delta.svg"), 7.0),
    }
    categories = "\n".join(
        f'      <category value="{val}" label="{label}" symbol="{sid}" render="true"/>'
        for sid, (val, label, _, _) in icons.items()
    )
    symbols = "\n".join(
        f'      <symbol name="{sid}" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">\n'
        f"{svg_marker(data, size)}\n      </symbol>"
        for sid, (_, _, data, size) in icons.items()
    )
    return f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34.0" styleCategories="Symbology|Labeling">
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
</qgis>
"""


def build_stations() -> str:
    data = b64("rail_station.svg")
    return f"""<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.34.0" styleCategories="Symbology|Labeling">
  <renderer-v2 type="singleSymbol" symbollevels="0">
    <symbols>
      <symbol name="0" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
{svg_marker(data, 5.5)}
      </symbol>
    </symbols>
  </renderer-v2>
{labeling(6.5, 50, "52,73,94,255", 1.0)}
</qgis>
"""


def main() -> None:
    (HERE / "poi_destinations.qml").write_text(build_poi(), encoding="utf-8")
    (HERE / "rail_stations.qml").write_text(build_stations(), encoding="utf-8")
    print("geschrieben: poi_destinations.qml, rail_stations.qml (mit eingebetteten SVGs)")


if __name__ == "__main__":
    main()
