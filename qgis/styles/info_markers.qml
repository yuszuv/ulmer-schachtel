<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!-- Stil für: info_markers (Punkt-Layer)
     Handgepflegt: diese Datei direkt bearbeiten (nicht generiert).

     Ein einzelner ℹ-Marker in der Mitte Rumäniens — dient als interaktive
     Legende/Hilfe: Antippen in QField → HTML-Karte mit Erklärung der Symbole,
     Navigationshinweisen und dem Hinweis zum Donaudelta (nicht per Bahn erreichbar).

     Symbologie: türkisfarbener Kreis (47,107,107) mit cremefarbenem Rand (#f3ecd5).
     Label: kursives „i" in Creme, immer sichtbar (displayAll="1").
     Map Tip: Felder „title" (fett) und „body" (Freitext) aus dem GeoJSON.

     WICHTIG beim Laden in QGIS:
       Layer Properties → Style → Load Style → „All Categories" auswählen.
       Danach Display-Feld auf „title" setzen (Layer Properties → Display). -->
<qgis version="3.34.0" styleCategories="Symbology|Labeling|MapTips">
  <renderer-v2 type="singleSymbol" symbollevels="0">
    <symbols>
      <symbol name="0" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
        <layer class="SimpleMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="size" type="QString" value="4.2"/>
            <Option name="color" type="QString" value="47,107,107,255"/>
            <Option name="outline_color" type="QString" value="243,236,213,255"/>
            <Option name="outline_width" type="QString" value="0.6"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <!-- Beschriftung: kursives „i" als festes Literal, nicht als Attributfeld.
       fieldName="'i'" + isExpression="1" = QGIS-Ausdruck, der immer „i" ergibt —
         kein Attribut namens „i" nötig, der Text ist hartcodiert.
       fontItalic="1" = kursiv für das klassische ℹ-Erscheinungsbild.
       textColor="243,236,213,255" = cremefarbener Text auf türkisem Kreis.
       placement="1" = Over Point (Text über dem Marker-Mittelpunkt, nicht daneben).
       displayAll="1" = immer sichtbar, keine automatische Unterdrückung bei
         Überlappungen (sinnvoll: es gibt genau einen ℹ-Marker in der ganzen Karte). -->
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fieldName="'i'" isExpression="1"
                  fontFamily="Sans Serif" fontSize="7" fontSizeUnit="Point"
                  fontWeight="75" namedStyle="Bold" fontItalic="1"
                  fontUnderline="0" fontStrikeout="0" fontKerning="1"
                  fontLetterSpacing="0" fontWordSpacing="0"
                  textColor="243,236,213,255" textOpacity="1" blendMode="0"
                  multilineHeight="1" multilineHeightUnit="Percentage"
                  textOrientation="horizontal" capitalization="0"
                  allowHtml="0" useSubstitutions="0"
                  previewBkgrdColor="255,255,255,255" legendString="Aa"
                  fontSizeMapUnitScale="3x:0,0,0,0,0,0"/>
      <text-format wrapChar="" autoWrapLength="0" useMaxLineLengthForAutoWrap="1"
                   multilineAlign="3" addDirectionSymbol="0"
                   leftDirectionSymbol="&lt;" rightDirectionSymbol=">"
                   reverseDirectionSymbol="0" placeDirectionSymbol="0"
                   formatNumbers="0" decimals="3" plusSign="0"/>
      <placement placement="1" dist="0" distUnits="MM"
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
      <rendering drawLabels="1" displayAll="1" limitNumLabels="0"
                 maxNumLabels="2000" minFeatureSize="0"
                 fontLimitPixelSize="0" fontMinPixelSize="3" fontMaxPixelSize="10000"
                 scaleVisibility="0" scaleMin="1" scaleMax="10000000"
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
  <!-- Map Tip: HTML-Karte beim Antippen in QGIS / QField (Identify / Finger-Tap).
       CDATA schützt HTML-Sonderzeichen (<, >, &) vor XML-Interpretation.
       [% "title" %] und [% "body" %] = QGIS-Expressions → werden durch die
         gleichnamigen Felder aus info_markers.geojson ersetzt.
         "body" darf selbst HTML enthalten (Fettdruck, Zeilenumbrüche usw.).
       WICHTIG: nur aktiv wenn Style mit "All Categories" geladen wurde. -->
  <mapTip><![CDATA[<div style="font-family:serif;color:#39312b;max-width:260px">
  <div style="font-size:14px;font-weight:bold;color:#2f6b6b">[% "title" %]</div>
  <div style="font-size:12px;margin-top:4px">[% "body" %]</div>
</div>]]></mapTip>
</qgis>
