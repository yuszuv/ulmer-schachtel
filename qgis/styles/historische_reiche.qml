<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!-- Stil für: historische_reiche / Layer „Historische Reiche" (Polygon-Layer)
     Handgepflegt: diese Datei direkt bearbeiten (nicht generiert).

     WAS ZEIGT DIESE EBENE?
       Die 9 historischen Regionen, aufgelöst nach EMPIRE → genau 2 Flächen
       (Österreich-Ungarn, Königreich Rumänien). Erzeugt von
       tools/fetch_historical_regions.py (build_empires, ogr2ogr ST_Union).

     ZWECK — reine BESCHRIFTUNGS-Ebene: labelt jedes Reich GENAU EINMAL.
       Die Regionen-Ebene (historische_regionen) hat 9 Einzelpolygone; ein
       EMPIRE-Label dort erschiene 4×/4×. Diese gemergte Ebene löst das: ein
       MultiPolygon pro Reich + labelPerPart=0 → ein einziges, zentriertes Label.

     SYMBOLOGIE — keine Füllung, keine Outline (die Färbung kommt von der
       Regionen-Ebene darunter). Nur der Schriftzug ist sichtbar.

     MASSSTAB — Reichs-Label bei mittlerem Zoom, wo die Regionen erscheinen:
       Labels 1:5 Mio … 1:1 Mio (gröber als Regionsnamen, früher sichtbar).

     WICHTIG beim Laden in QGIS:
       Layer Properties → Style → Load Style → „All Categories" auswählen. -->
<qgis version="3.34.0" styleCategories="Symbology|Labeling">
  <!-- Unsichtbare Füllung — diese Ebene liefert nur das Label. -->
  <renderer-v2 type="singleSymbol" symbollevels="0" forceraster="0" enableorderby="0">
    <symbols>
      <symbol name="0" type="fill" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleFill" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="style" type="QString" value="no"/>
            <Option name="outline_style" type="QString" value="no"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <!-- Beschriftung: EMPIRE in Kapitälchen, größer als Regionsnamen.
       labelPerPart="0" = ein Label je (Multi-)Polygon, nicht pro Teilfläche.
       centroidInside="1" = Label-Anker innerhalb der Fläche (auch bei konkav). -->
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fieldName="EMPIRE" isExpression="0"
                  fontFamily="Sans Serif" fontSize="11" fontSizeUnit="Point"
                  fontWeight="75" namedStyle="Bold" fontItalic="0"
                  fontUnderline="0" fontStrikeout="0" fontKerning="1"
                  fontLetterSpacing="2.0" fontWordSpacing="0"
                  textColor="107,79,42,255" textOpacity="1" blendMode="0"
                  multilineHeight="1" multilineHeightUnit="Percentage"
                  textOrientation="horizontal" capitalization="2"
                  allowHtml="0" useSubstitutions="0"
                  previewBkgrdColor="255,255,255,255" legendString="Aa"
                  fontSizeMapUnitScale="3x:0,0,0,0,0,0">
        <text-buffer bufferDraw="1" bufferSize="1.4" bufferSizeUnits="MM"
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
                 rotationAngle="0" rotationUnit="AngleDegrees" priority="8"
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
                 scaleVisibility="1" scaleMin="5000000" scaleMax="1000000"
                 obstacle="0" obstacleFactor="1" obstacleType="0"
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
