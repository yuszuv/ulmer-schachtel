<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!-- Stil für: historische_staedte / Layer „Historische Städte" (Punkt-Layer)
     Handgepflegt: diese Datei direkt bearbeiten (nicht generiert).

     WAS ZEIGT DIESE EBENE?
       25 handkuratierte historische Städte in den Regionen Österreich-Ungarns
       und des Königreichs Rumänien um ~1900, mit deutschen, ungarischen und
       modernen rumänischen Namen.

     RENDERER — SingleSymbol: kleiner Sepia-Kreis mit heller Umrandung.
       Unterscheidet nicht nach Region/Reich — die Regionszugehörigkeit leuchtet
       aus der darunterliegenden Regionen-Ebene hervor. Marker ist kleiner als
       Bahnhöfe (3 mm vs. 5 mm), da er rein historische Orientierung liefert.

     BESCHRIFTUNG — NAME (modern, z. B. „Brașov"), dann NAME_DE kursiv darunter.
       Der Ausdruck verbindet die beiden Felder: moderner Name fett, historischer
       deutsch-kursiv in Klammern — klassischer Atlas-Look.

     MASSSTAB:
       Layer sichtbar 1:1,5 Mio … nah (analog Bahnhöfe).
       Labels ab 1:1 Mio sichtbar.

     WICHTIG beim Laden in QGIS:
       Layer Properties → Style → Load Style → „All Categories" auswählen. -->
<qgis version="3.34.0" styleCategories="Symbology|Labeling|MapTips">
  <!-- SingleSymbol: sepia gefüllter Kreis, halbtransparenter Canvas-Halo. -->
  <renderer-v2 type="singleSymbol" symbollevels="0" forceraster="0" enableorderby="0">
    <symbols>
      <symbol name="0" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- Äußerer Ring: helle Umrandung (#f3ecd5, Palette-Hintergrund) -->
        <layer class="SimpleMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="107,79,42,220"/>
            <Option name="outline_color" type="QString" value="243,236,213,220"/>
            <Option name="outline_width" type="QString" value="0.6"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="3.0"/>
            <Option name="size_unit" type="QString" value="MM"/>
            <Option name="angle" type="QString" value="0"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="scale_method" type="QString" value="diameter"/>
            <Option name="joinstyle" type="QString" value="bevel"/>
            <Option name="horizontal_anchor_point" type="QString" value="1"/>
            <Option name="vertical_anchor_point" type="QString" value="1"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
    <rotation/>
    <sizescale/>
  </renderer-v2>
  <!-- Beschriftung: NAME (modern) fett, dazu NAME_DE kursiv in Klammern wenn vorhanden.
       Expression: if("NAME_DE" != '', "NAME" || ' (' || "NAME_DE" || ')', "NAME")
       Sepia-Schrift #6b4f2a, Semi-transparenter Halo für Lesbarkeit. -->
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style isExpression="1"
                  fieldName="if( &quot;NAME_DE&quot; != '', &quot;NAME&quot; || ' (' || &quot;NAME_DE&quot; || ')', &quot;NAME&quot;  )"
                  fontFamily="Sans Serif" fontSize="7" fontSizeUnit="Point"
                  fontWeight="75" namedStyle="Bold" fontItalic="0"
                  fontUnderline="0" fontStrikeout="0" fontKerning="1"
                  fontLetterSpacing="0" fontWordSpacing="0"
                  textColor="90,62,27,255" textOpacity="1" blendMode="0"
                  multilineHeight="1" multilineHeightUnit="Percentage"
                  textOrientation="horizontal" capitalization="0"
                  allowHtml="0" useSubstitutions="0"
                  previewBkgrdColor="255,255,255,255" legendString="Aa"
                  fontSizeMapUnitScale="3x:0,0,0,0,0,0">
        <text-buffer bufferDraw="1" bufferSize="0.9" bufferSizeUnits="MM"
                     bufferColor="243,236,213,210" bufferOpacity="1"
                     bufferJoinStyle="64" bufferNoFill="1" bufferBlendMode="0"/>
      </text-style>
      <text-format wrapChar="" autoWrapLength="0" useMaxLineLengthForAutoWrap="1"
                   multilineAlign="3" addDirectionSymbol="0"
                   leftDirectionSymbol="&lt;" rightDirectionSymbol=">"
                   reverseDirectionSymbol="0" placeDirectionSymbol="0"
                   formatNumbers="0" decimals="3" plusSign="0"/>
      <placement placement="0" dist="1.5" distUnits="MM"
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
                 scaleVisibility="1" scaleMin="0" scaleMax="1000000"
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
  <!-- Map Tip: Multilingual Stadtkarte beim Antippen (QGIS / QField Identify). -->
  <mapTip><![CDATA[<div style="font-family:serif;color:#39312b;max-width:280px">
<div style="font-size:15px;font-weight:bold;color:#5a3e1b">[% "NAME" %]</div>
[% if( "NAME_DE" != '', '<div style="font-size:12px;font-style:italic;color:#6b4f2a">de: ' || "NAME_DE" || '</div>', '') %]
[% if( "NAME_HU" != '', '<div style="font-size:12px;font-style:italic;color:#6b4f2a">hu: ' || "NAME_HU" || '</div>', '') %]
<div style="font-size:11px;color:#888;margin-top:4px">[% "REGION" %] · <b>[% "EMPIRE" %]</b></div>
<div style="font-size:11px;margin-top:6px">[% "NOTE" %]</div>
</div>]]></mapTip>
</qgis>
