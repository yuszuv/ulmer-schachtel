<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!-- Stil für: staatsgrenzen / Layer „Grenzen 1800" (Polygon-Layer)
     Handgepflegt: diese Datei direkt bearbeiten (nicht generiert).

     WAS ZEIGT DIESE EBENE?
       Historische Staatsgrenzen um ~1880–1900 (Weltdatensatz, 236 Features).
       Auf dieser Karte ist sie die Reise-Story: Um 1900 gehörten Siebenbürgen
       (Brașov, Sighișoara, Cluj) und das Banat (Timișoara) zu ÖSTERREICH-UNGARN,
       während das KÖNIGREICH RUMÄNIEN (Walachei + Moldau, „Regat") ein eigener
       Staat war. Die CFR-Bahnreise überquert genau diese alte Grenze.

     RENDERER — RuleRenderer mit drei narrativen Stufen (statt der früheren,
     visuell wirkungslosen Kategorisierung):
       A) Österreich-Ungarn — gedämpft goldocker getönt (Hauptakteur).
       B) Königreich Rumänien — gedämpft oliv getönt (Hauptakteur, Reise-Ziel).
       C) Balkan-Nachbarn (Osmanen, Bulgarien, Serbien, Montenegro,
          Bosnien-Herzegowina, Griechenland, Russland) — nur gestrichelte
          Sepia-Umrisse, als Kontextrahmen.
       Der Welt-Rest hat keine Regel → wird nicht gezeichnet (und ist zusätzlich
       per Subset-String in tools/qgis_bootstrap.py weggefiltert).

     FARBEN (~30 % Deckkraft → Basemap scheint durch). Wo die Projekt-Palette
     greift, wird sie genutzt; die getönten Flächen sind bewusste, sepia-verwandte
     Erweiterungen für die Story-Ebene (siehe styles/README.md):
       AT-Ungarn   Füllung #c8a96e (200,169,110) @ alpha 77, Outline #6b4f2a (Palette)
       Rumänien    Füllung #8faf7a (143,175,122) @ alpha 77, Outline #4a6b35 (grün, Story)
       Nachbarn    keine Füllung,                          Outline #9c7a5a dash
       Label-Text  #6b4f2a (Palette-Sepia), Halo #f3ecd5 (Palette-Hintergrund)

     MASSSTAB — Grenzen sind bei Weitzoom Orientierungsrahmen, bei Nahzoom Lärm:
       Layer sichtbar 1:800k … 1:20 Mio (hasScaleBasedVisibilityFlag=1).
       Labels nur 1:2 Mio … 1:15 Mio.

     WICHTIG beim Laden in QGIS:
       Layer Properties → Style → Load Style → „All Categories" auswählen,
       sonst wird die Beschriftung nicht übernommen. -->
<qgis version="3.34.0" styleCategories="Symbology|Labeling"
      hasScaleBasedVisibilityFlag="1" minScale="20000000" maxScale="800000">
  <renderer-v2 type="RuleRenderer" symbollevels="0" forceraster="0" enableorderby="0">
    <rules key="{b0000000-0000-0000-0000-000000000000}">
      <!-- Stufe A: Österreich-Ungarn (goldocker) -->
      <rule key="{a1000000-0000-0000-0000-000000000001}" symbol="0"
            label="Österreich-Ungarn" filter="&quot;NAME&quot; = 'Austria Hungary'"/>
      <!-- Stufe B: Königreich Rumänien (oliv) -->
      <rule key="{a1000000-0000-0000-0000-000000000002}" symbol="1"
            label="Königreich Rumänien" filter="&quot;NAME&quot; = 'Romania'"/>
      <!-- Stufe C: Balkan-Nachbarn (nur gestrichelte Umrisse) -->
      <rule key="{a1000000-0000-0000-0000-000000000003}" symbol="2"
            label="Nachbarstaaten"
            filter="&quot;NAME&quot; IN ('Ottoman Empire','Bulgaria','Serbia','Montenegro','Bosnia-Herzegovina','Greece','Russian Empire')"/>
    </rules>
    <symbols>
      <!-- symbol 0 = Österreich-Ungarn: goldocker Füllung + dunkle Sepia-Outline -->
      <symbol name="0" type="fill" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="color" type="QString" value="200,169,110,77"/>
            <Option name="style" type="QString" value="solid"/>
            <Option name="outline_color" type="QString" value="107,79,42,255"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="1.5"/>
            <Option name="outline_width_unit" type="QString" value="Point"/>
            <Option name="joinstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <!-- symbol 1 = Königreich Rumänien: oliv Füllung + dunkelgrüne Outline -->
      <symbol name="1" type="fill" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="color" type="QString" value="143,175,122,77"/>
            <Option name="style" type="QString" value="solid"/>
            <Option name="outline_color" type="QString" value="74,107,53,255"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="1.5"/>
            <Option name="outline_width_unit" type="QString" value="Point"/>
            <Option name="joinstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <!-- symbol 2 = Nachbarstaaten: keine Füllung, gestrichelte Sepia-Outline -->
      <symbol name="2" type="fill" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="style" type="QString" value="no"/>
            <Option name="outline_color" type="QString" value="156,122,90,255"/>
            <Option name="outline_style" type="QString" value="dash"/>
            <Option name="outline_width" type="QString" value="1.0"/>
            <Option name="outline_width_unit" type="QString" value="Point"/>
            <Option name="joinstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <!-- Beschriftung: Ländername (NAME), Großbuchstaben für historischen Atlas-Look.
       Sepia-Schrift #5a3e1b mit hellem Canvas-Halo (#f3ecd5) für Lesbarkeit über
       der getönten Fläche und der Basemap. Nur im Band 1:2 Mio … 1:15 Mio sichtbar:
       weiter draußen sind die Polygone zu klein, weiter drin liest man Städtenamen.
       capitalization="2" = Alle Großbuchstaben. -->
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fieldName="NAME" isExpression="0"
                  fontFamily="Sans Serif" fontSize="8" fontSizeUnit="Point"
                  fontWeight="50" namedStyle="Regular" fontItalic="0"
                  fontUnderline="0" fontStrikeout="0" fontKerning="1"
                  fontLetterSpacing="0.5" fontWordSpacing="0"
                  textColor="107,79,42,255" textOpacity="1" blendMode="0"
                  multilineHeight="1" multilineHeightUnit="Percentage"
                  textOrientation="horizontal" capitalization="2"
                  allowHtml="0" useSubstitutions="0"
                  previewBkgrdColor="255,255,255,255" legendString="Aa"
                  fontSizeMapUnitScale="3x:0,0,0,0,0,0">
        <text-buffer bufferDraw="1" bufferSize="1.2" bufferSizeUnits="MM"
                     bufferColor="243,236,213,200" bufferOpacity="1"
                     bufferJoinStyle="64" bufferNoFill="1" bufferBlendMode="0"/>
      </text-style>
      <text-format wrapChar="" autoWrapLength="0" useMaxLineLengthForAutoWrap="1"
                   multilineAlign="3" addDirectionSymbol="0"
                   leftDirectionSymbol="&lt;" rightDirectionSymbol=">"
                   reverseDirectionSymbol="0" placeDirectionSymbol="0"
                   formatNumbers="0" decimals="3" plusSign="0"/>
      <placement placement="0" dist="0" distUnits="MM"
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
                 fitInPolygonOnly="0" centroidWhole="0" centroidInside="1"
                 pointOnSurface="0" pointOnAllParts="0"
                 geometryGeneratorEnabled="0" geometryGeneratorType="PointGeometry"
                 geometryGenerator="" layerType="PolygonGeometry"
                 overrunDistance="0" overrunDistanceUnit="MM"
                 overrunDistanceMapUnitScale="3x:0,0,0,0,0,0"
                 lineAnchorPercent="0.5" lineAnchorType="0" lineAnchorClipping="0"
                 polygonPlacementFlags="2" allowDegraded="0"
                 mLineDistance="0" mLineDistanceUnit="MM"
                 mLineDistanceMapUnitScale="3x:0,0,0,0,0,0"/>
      <rendering drawLabels="1" displayAll="0" limitNumLabels="0"
                 maxNumLabels="2000" minFeatureSize="0"
                 fontLimitPixelSize="0" fontMinPixelSize="3" fontMaxPixelSize="10000"
                 scaleVisibility="1" scaleMin="2000000" scaleMax="15000000"
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
</qgis>
