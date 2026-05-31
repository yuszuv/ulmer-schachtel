<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!-- Stil für: historische_regionen / Layer „Historische Regionen" (Polygon-Layer)
     Handgepflegt: diese Datei direkt bearbeiten (nicht generiert).

     WAS ZEIGT DIESE EBENE?
       Die 9 historischen Großregionen um ~1900 (Siebenbürgen, Banat, Crișana,
       Maramureș, Bukowina, Moldau, Muntenia, Oltenien, Dobrudscha), konstruiert
       aus Natural Earth admin-1 (public domain). Bezirke über zwei Staaten hinweg
       (Banat: RO + RS, Bukowina: RO + UA) liegen als aufgelöste Polygone vor.

     RENDERER — RuleRenderer, zwei narrative Stufen nach EMPIRE:
       A) Österreich-Ungarn — goldocker getönt (wie Grenzen 1800, aber heller).
       B) Königreich Rumänien — oliv getönt (wie Grenzen 1800, aber heller).
       Farben identisch mit grenzen.qml (Story-Palette), aber halbe Deckkraft
       (alpha 40 ≈ 16 %), damit die unterliegende Staatsgrenzen-Ebene spürbar
       bleibt und die Regionen nur feine Binnenstruktur beisteuern.

     MASSSTAB — Regionen erscheinen beim Hineinzoomen unter die Staatsebene:
       Layer sichtbar 1:3 Mio … 1:200k.
       Labels nur 1:1,5 Mio … 1:200k (enger, gegen Überlappung mit Ländernamen).

     WICHTIG beim Laden in QGIS:
       Layer Properties → Style → Load Style → „All Categories" auswählen. -->
<qgis version="3.34.0" styleCategories="Symbology|Labeling|MapTips"
      hasScaleBasedVisibilityFlag="1" minScale="3000000" maxScale="200000">
  <renderer-v2 type="RuleRenderer" symbollevels="0" forceraster="0" enableorderby="0">
    <rules key="{c0000000-0000-0000-0000-000000000000}">
      <!-- Stufe A: Österreich-Ungarn (goldocker, wie grenzen.qml) -->
      <rule key="{c1000000-0000-0000-0000-000000000001}" symbol="0"
            label="Österreich-Ungarn"
            filter="&quot;EMPIRE&quot; = 'Österreich-Ungarn'"/>
      <!-- Stufe B: Königreich Rumänien (oliv, wie grenzen.qml) -->
      <rule key="{c1000000-0000-0000-0000-000000000002}" symbol="1"
            label="Königreich Rumänien"
            filter="&quot;EMPIRE&quot; = 'Königreich Rumänien'"/>
    </rules>
    <symbols>
      <!-- symbol 0 = Österreich-Ungarn: goldocker Füllung (alpha 40, heller als Grenzen)
           + dünne Sepia-Outline. Palette: #c8a96e, Outline #6b4f2a (Hauptpalette). -->
      <symbol name="0" type="fill" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="color" type="QString" value="200,169,110,40"/>
            <Option name="style" type="QString" value="solid"/>
            <Option name="outline_color" type="QString" value="107,79,42,180"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.8"/>
            <Option name="outline_width_unit" type="QString" value="Point"/>
            <Option name="joinstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
      <!-- symbol 1 = Königreich Rumänien: oliv Füllung (alpha 40) + grüne Outline. -->
      <symbol name="1" type="fill" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="color" type="QString" value="143,175,122,40"/>
            <Option name="style" type="QString" value="solid"/>
            <Option name="outline_color" type="QString" value="74,107,53,180"/>
            <Option name="outline_style" type="QString" value="solid"/>
            <Option name="outline_width" type="QString" value="0.8"/>
            <Option name="outline_width_unit" type="QString" value="Point"/>
            <Option name="joinstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <!-- Beschriftung: Regionsname (NAME) in Kapitälchen; kursiv für historischen
       Atlas-Charakter. Sepia-Schrift #6b4f2a, halbtransparenter Halo #f3ecd5.
       Maßstab: Labels erst ab 1:1,5 Mio sichtbar (ab da lesen sich Regionsnamen
       besser als Ländernamen). -->
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fieldName="NAME" isExpression="0"
                  fontFamily="Sans Serif" fontSize="7" fontSizeUnit="Point"
                  fontWeight="50" namedStyle="Italic" fontItalic="1"
                  fontUnderline="0" fontStrikeout="0" fontKerning="1"
                  fontLetterSpacing="1.0" fontWordSpacing="0"
                  textColor="107,79,42,255" textOpacity="1" blendMode="0"
                  multilineHeight="1" multilineHeightUnit="Percentage"
                  textOrientation="horizontal" capitalization="2"
                  allowHtml="0" useSubstitutions="0"
                  previewBkgrdColor="255,255,255,255" legendString="Aa"
                  fontSizeMapUnitScale="3x:0,0,0,0,0,0">
        <text-buffer bufferDraw="1" bufferSize="1.0" bufferSizeUnits="MM"
                     bufferColor="243,236,213,180" bufferOpacity="1"
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
                 scaleVisibility="1" scaleMin="1500000" scaleMax="200000"
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
  <!-- Map Tip: erscheint beim Antippen des Polygons in QGIS / QField.
       Zeigt deutsche + lokale Namen, Reich, Hinweis. -->
  <mapTip><![CDATA[<div style="font-family:serif;color:#39312b;max-width:280px">
<div style="font-size:15px;font-weight:bold;color:#6b4f2a">[% "NAME" %]</div>
<div style="font-size:11px;font-style:italic;color:#888;margin-top:2px">[% "NAME_LOCAL" %]</div>
<div style="font-size:11px;color:#5a3e1b;margin-top:4px"><b>[% "EMPIRE" %]</b></div>
<div style="font-size:11px;margin-top:6px">[% "NOTE" %]</div>
</div>]]></mapTip>
</qgis>
