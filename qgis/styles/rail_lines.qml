<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!-- Stil für: rail_lines (Linien-Layer)
     Handgepflegt: diese Datei direkt bearbeiten (nicht generiert).

     SYMBOLOGIE — Eisenbahn-Signatur angelehnt an amtliche Topokarten (DTK10/DTK100):
       Schwarze Volllinie als „Gleis" + weiße gestrichelte Decklinie als „Schwellen".
       Umgesetzt als zwei übereinander gestapelte Linien-Layer (symbollevels="1").
       pass="0" = untere Schicht (Gleis), pass="1" = obere Schicht (Schwellen).

     BESCHRIFTUNG — route_id (z.B. „M300") gebogen entlang der Strecke.
       placement="3" = Curved (folgt der Linienkrümmung).
       repeatDistance="40mm" = Label wiederholt sich bei langen Linien.

     MAP TIP — Fahrplan-Daten beim Antippen: Strecke, Zeiten, Zug, Via.
       Die Felder (dep_time, arr_time usw.) stammen aus data/processed/timetable.csv
       (hand-gepflegt) und werden von tools/fetch_cfr_data.py per route_id in die
       rail_lines.geojson eingebettet. Felder, die noch nicht eingetragen wurden,
       zeigen „–" dank coalesce() — kein Fehler.

     WICHTIG beim Laden in QGIS:
       Layer Properties → Style → Load Style → „All Categories" auswählen.
       Sonst werden Beschriftung und Map Tip nicht übernommen. -->
<qgis version="3.34.0" styleCategories="Symbology|Labeling|MapTips">
  <renderer-v2 type="singleSymbol" symbollevels="1">
    <symbols>
      <symbol name="0" type="line" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- Layer 1: schwarzes Gleisband (pass=0 → wird zuerst gezeichnet) -->
        <layer class="SimpleLine" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="line_color" type="QString" value="0,0,0,255"/>
            <Option name="line_width" type="QString" value="1.4"/>
            <Option name="line_width_unit" type="QString" value="Point"/>
            <Option name="line_style" type="QString" value="solid"/>
            <Option name="capstyle" type="QString" value="flat"/>
            <Option name="joinstyle" type="QString" value="round"/>
          </Option>
        </layer>
        <!-- Layer 2: weiße Schwellen-Sprossen (pass=1 → darüber gezeichnet)
             customdash "1.4;3" bedeutet: 1.4mm Strich, 3mm Lücke -->
        <layer class="SimpleLine" enabled="1" pass="1" locked="0">
          <Option type="Map">
            <Option name="line_color" type="QString" value="255,255,255,255"/>
            <Option name="line_width" type="QString" value="1.1"/>
            <Option name="line_width_unit" type="QString" value="Point"/>
            <Option name="line_style" type="QString" value="dash"/>
            <Option name="use_custom_dash" type="QString" value="1"/>
            <Option name="customdash" type="QString" value="1.4;3"/>
            <Option name="customdash_unit" type="QString" value="MM"/>
            <Option name="capstyle" type="QString" value="flat"/>
            <Option name="joinstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <!-- Beschriftung: route_id gebogen entlang der Strecke.
       placement="3" = Curved — Labels folgen der Linienkrümmung.
       repeatDistance="40" = Label alle 40mm wiederholen (sinnvoll für lange Strecken).
       bufferDraw="1" = weißer Hintergrund-Puffer für Lesbarkeit auf bunten Kacheln.
       Farbton 107,79,42 = gedämpftes Sepiabraun (konsistent zur Farbpalette). -->
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fieldName="route_id" isExpression="0"
                  fontFamily="Sans Serif" fontSize="7.5" fontSizeUnit="Point"
                  fontWeight="75" namedStyle="Bold" fontItalic="0"
                  fontUnderline="0" fontStrikeout="0" fontKerning="1"
                  fontLetterSpacing="0" fontWordSpacing="0"
                  textColor="107,79,42,255" textOpacity="1" blendMode="0"
                  multilineHeight="1" multilineHeightUnit="Percentage"
                  textOrientation="horizontal" capitalization="0"
                  allowHtml="0" useSubstitutions="0"
                  previewBkgrdColor="255,255,255,255" legendString="Aa"
                  fontSizeMapUnitScale="3x:0,0,0,0,0,0">
        <text-buffer bufferDraw="1" bufferSize="0.6" bufferSizeUnits="MM"
                     bufferColor="255,255,255,220" bufferOpacity="1"
                     bufferJoinStyle="64" bufferNoFill="0" bufferBlendMode="0"/>
      </text-style>
      <text-format wrapChar="" autoWrapLength="0" useMaxLineLengthForAutoWrap="1"
                   multilineAlign="3" addDirectionSymbol="0"
                   leftDirectionSymbol="&lt;" rightDirectionSymbol=">"
                   reverseDirectionSymbol="0" placeDirectionSymbol="0"
                   formatNumbers="0" decimals="3" plusSign="0"/>
      <placement placement="3" dist="0" distUnits="MM"
                 distMapUnitScale="3x:0,0,0,0,0,0"
                 quadOffset="4" offsetType="0" xOffset="0" yOffset="0"
                 offsetUnits="MM" xOffsetMapUnitScale="3x:0,0,0,0,0,0"
                 yOffsetMapUnitScale="3x:0,0,0,0,0,0"
                 labelOffsetMapUnitScale="3x:0,0,0,0,0,0"
                 rotationAngle="0" rotationUnit="AngleDegrees" priority="5"
                 repeatDistance="40" repeatDistanceUnit="MM"
                 repeatDistanceMapUnitScale="3x:0,0,0,0,0,0"
                 maxCurvedCharAngleIn="25" maxCurvedCharAngleOut="-25"
                 predefinedPositionOrder="TR,TL,BR,BL,R,L,TSR,BSR"
                 fitInPolygonOnly="0" centroidWhole="0" centroidInside="0"
                 pointOnSurface="0" pointOnAllParts="0"
                 geometryGeneratorEnabled="0" geometryGeneratorType="PointGeometry"
                 geometryGenerator="" layerType="LineGeometry"
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
  </labeling>
  <!-- Map Tip: HTML-Karte beim Antippen in QGIS / QField.
       [% "feldname" %] = QGIS-Expression → wird durch Attributwert ersetzt.
       coalesce("feld", '–') zeigt „–" wenn das Feld NULL oder leer ist.
       Die Timetable-Felder (dep_time, arr_time usw.) sind leer bis sie in
       data/processed/timetable.csv eingetragen + fetch_cfr_data.py neu ausgeführt
       + build-gpkg gebaut wurden. -->
  <mapTip><![CDATA[<div style="font-family:serif;color:#39312b;max-width:280px">
  <div style="font-size:14px;font-weight:bold;color:#6b4f2a">[% "route_id" %] – [% "route_name" %]</div>
  <div style="font-size:12px;margin-top:4px">[% "from_city" %] → [% "to_city" %]</div>
  <div style="font-size:11px;color:#888;margin-top:6px">
    <b>Tage:</b> [% coalesce("days", '–') %]<br>
    <b>Abf.:</b> [% coalesce("dep_time", '–') %] &nbsp;
    <b>Ank.:</b> [% coalesce("arr_time", '–') %] &nbsp;
    <b>Dauer:</b> [% coalesce("duration", '–') %]<br>
    <b>Zug:</b> [% coalesce("train", '–') %]<br>
    <b>Via:</b> [% coalesce("via", '–') %]
  </div>
</div>]]></mapTip>
</qgis>
