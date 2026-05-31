<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Style für: wikivoyage_cities (Punkt-Layer)
  Generiert von: qgis/styles/build_marker_styles.py
  Nicht manuell bearbeiten — Änderungen werden beim nächsten Generieren
  überschrieben. Stattdessen build_marker_styles.py anpassen, dann neu ausführen.
-->
<qgis version="3.34.0" styleCategories="Symbology|Labeling|MapTips">
  <!-- Renderer: RuleRenderer — one rule per historical region.
       Each rule filters on the "region" attribute and picks its marker colour via
       symbol="…". scalemaxdenom makes all cities appear at 1:2000000
       inward (avoids cluster clutter at continental zoom). Colour-coded instead
       of icons: the region is immediately legible from the colour (legend = regions). -->
  <renderer-v2 type="RuleRenderer" symbollevels="0">
    <rules key="{wv-rules}">
      <rule symbol="0" filter="&quot;region&quot; = 'Banat'" scalemaxdenom="2000000" label="Banat" key="{wv-rule-0}"/>
      <rule symbol="1" filter="&quot;region&quot; = 'Kreischgebiet'" scalemaxdenom="2000000" label="Kreischgebiet" key="{wv-rule-1}"/>
      <rule symbol="2" filter="&quot;region&quot; = 'Sathmar/Marmarosch'" scalemaxdenom="2000000" label="Sathmar/Marmarosch" key="{wv-rule-2}"/>
      <rule symbol="3" filter="&quot;region&quot; = 'Siebenbürgen'" scalemaxdenom="2000000" label="Siebenbürgen" key="{wv-rule-3}"/>
      <rule symbol="4" filter="&quot;region&quot; = 'Walachei (Muntenia)'" scalemaxdenom="2000000" label="Walachei (Muntenia)" key="{wv-rule-4}"/>
      <rule symbol="5" filter="&quot;region&quot; = 'Walachei (Oltenia)'" scalemaxdenom="2000000" label="Walachei (Oltenia)" key="{wv-rule-5}"/>
      <rule symbol="6" filter="&quot;region&quot; = 'Moldau'" scalemaxdenom="2000000" label="Moldau" key="{wv-rule-6}"/>
      <rule symbol="7" filter="&quot;region&quot; = 'Bukowina'" scalemaxdenom="2000000" label="Bukowina" key="{wv-rule-7}"/>
      <rule symbol="8" filter="&quot;region&quot; = 'Dobrudscha'" scalemaxdenom="2000000" label="Dobrudscha" key="{wv-rule-8}"/>
    </rules>
    <symbols>
      <symbol name="0" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- SimpleMarker: filled circle, colour encodes category.
             No SVG required — shape and fill are defined inline (unlike SvgMarker).
             outline_color = canvas cream (#f3ecd5) for contrast on coloured tiles.
             size_unit="MM" = device-independent; anchor_point="1" = centre. -->
        <layer class="SimpleMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="181,80,60,255"/>
            <Option name="outline_color" type="QString" value="243,236,213,255"/>
            <Option name="outline_width" type="QString" value="0.4"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="4.0"/>
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
      <symbol name="1" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- SimpleMarker: filled circle, colour encodes category.
             No SVG required — shape and fill are defined inline (unlike SvgMarker).
             outline_color = canvas cream (#f3ecd5) for contrast on coloured tiles.
             size_unit="MM" = device-independent; anchor_point="1" = centre. -->
        <layer class="SimpleMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="196,126,58,255"/>
            <Option name="outline_color" type="QString" value="243,236,213,255"/>
            <Option name="outline_width" type="QString" value="0.4"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="4.0"/>
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
      <symbol name="2" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- SimpleMarker: filled circle, colour encodes category.
             No SVG required — shape and fill are defined inline (unlike SvgMarker).
             outline_color = canvas cream (#f3ecd5) for contrast on coloured tiles.
             size_unit="MM" = device-independent; anchor_point="1" = centre. -->
        <layer class="SimpleMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="95,125,79,255"/>
            <Option name="outline_color" type="QString" value="243,236,213,255"/>
            <Option name="outline_width" type="QString" value="0.4"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="4.0"/>
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
      <symbol name="3" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- SimpleMarker: filled circle, colour encodes category.
             No SVG required — shape and fill are defined inline (unlike SvgMarker).
             outline_color = canvas cream (#f3ecd5) for contrast on coloured tiles.
             size_unit="MM" = device-independent; anchor_point="1" = centre. -->
        <layer class="SimpleMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="201,162,39,255"/>
            <Option name="outline_color" type="QString" value="243,236,213,255"/>
            <Option name="outline_width" type="QString" value="0.4"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="4.0"/>
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
      <symbol name="4" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- SimpleMarker: filled circle, colour encodes category.
             No SVG required — shape and fill are defined inline (unlike SvgMarker).
             outline_color = canvas cream (#f3ecd5) for contrast on coloured tiles.
             size_unit="MM" = device-independent; anchor_point="1" = centre. -->
        <layer class="SimpleMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="90,113,132,255"/>
            <Option name="outline_color" type="QString" value="243,236,213,255"/>
            <Option name="outline_width" type="QString" value="0.4"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="4.0"/>
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
      <symbol name="5" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- SimpleMarker: filled circle, colour encodes category.
             No SVG required — shape and fill are defined inline (unlike SvgMarker).
             outline_color = canvas cream (#f3ecd5) for contrast on coloured tiles.
             size_unit="MM" = device-independent; anchor_point="1" = centre. -->
        <layer class="SimpleMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="125,147,163,255"/>
            <Option name="outline_color" type="QString" value="243,236,213,255"/>
            <Option name="outline_width" type="QString" value="0.4"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="4.0"/>
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
      <symbol name="6" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- SimpleMarker: filled circle, colour encodes category.
             No SVG required — shape and fill are defined inline (unlike SvgMarker).
             outline_color = canvas cream (#f3ecd5) for contrast on coloured tiles.
             size_unit="MM" = device-independent; anchor_point="1" = centre. -->
        <layer class="SimpleMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="138,91,110,255"/>
            <Option name="outline_color" type="QString" value="243,236,213,255"/>
            <Option name="outline_width" type="QString" value="0.4"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="4.0"/>
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
      <symbol name="7" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- SimpleMarker: filled circle, colour encodes category.
             No SVG required — shape and fill are defined inline (unlike SvgMarker).
             outline_color = canvas cream (#f3ecd5) for contrast on coloured tiles.
             size_unit="MM" = device-independent; anchor_point="1" = centre. -->
        <layer class="SimpleMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="63,125,119,255"/>
            <Option name="outline_color" type="QString" value="243,236,213,255"/>
            <Option name="outline_width" type="QString" value="0.4"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="4.0"/>
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
      <symbol name="8" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- SimpleMarker: filled circle, colour encodes category.
             No SVG required — shape and fill are defined inline (unlike SvgMarker).
             outline_color = canvas cream (#f3ecd5) for contrast on coloured tiles.
             size_unit="MM" = device-independent; anchor_point="1" = centre. -->
        <layer class="SimpleMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="circle"/>
            <Option name="color" type="QString" value="168,144,72,255"/>
            <Option name="outline_color" type="QString" value="243,236,213,255"/>
            <Option name="outline_width" type="QString" value="0.4"/>
            <Option name="outline_width_unit" type="QString" value="MM"/>
            <Option name="size" type="QString" value="4.0"/>
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
  </renderer-v2>
  <!-- Beschriftung: Feld "name", Sans-Serif, mit weißem Hintergrund-Puffer.
       placement="0" = Around Point — QGIS sucht die beste Position rund um den Marker
         (für Linien wäre placement="3" = Curved).
       predefinedPositionOrder = Reihenfolge der geprüften Positionen: oben-rechts
         zuerst (TR), dann TL, BR, BL usw. — QGIS nimmt die erste überlappungsfreie.
       bufferDraw="1" + bufferColor "…,235" = leicht transparenter weißer Puffer
         hinter dem Text → Lesbarkeit auf bunten Kacheln deutlich besser.
       displayAll="0" = Labels werden unterdrückt wenn sie andere überdecken würden
         (Ausnahme info_markers: dort ist displayAll="1", weil es nur einen gibt).
       scaleVisibility="1" + scaleMax = Labels erscheinen erst ab diesem Maßstab
         nach innen (gegen Label-Cluster bei Kontinental-/Weitzoom). -->
  <labeling type="simple">
    <settings calloutType="simple">
      <text-style fieldName="name" isExpression="0"
                  fontFamily="Sans Serif" fontSize="7.5" fontSizeUnit="Point"
                  fontWeight="50" namedStyle="Regular" fontItalic="0"
                  fontUnderline="0" fontStrikeout="0" fontKerning="1"
                  fontLetterSpacing="0" fontWordSpacing="0"
                  textColor="57,49,43,255" textOpacity="1" blendMode="0"
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
      <placement placement="0" dist="1.2" distUnits="MM"
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
                 scaleVisibility="1" scaleMin="0" scaleMax="2000000"
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
  <!-- Map Tip: HTML-Karte beim Antippen in QGIS / QField (Identify / Finger-Tap).
       CDATA schützt HTML-Sonderzeichen (<, >, &) vor XML-Interpretation.
       [% "feldname" %] = QGIS-Expression → wird beim Anzeigen durch den
         tatsächlichen Attributwert ersetzt (z.B. [% "name" %] → "Brașov").
       WICHTIG: nur aktiv wenn Style mit "All Categories" geladen wurde. -->
  <mapTip><![CDATA[<div style="font-family:serif;color:#39312b;max-width:260px"><div style="font-size:14px;font-weight:bold;color:#6b4f2a">[% "name" %]</div><div style="font-size:11px;color:#888;margin-top:2px">[% "region" %]</div><div style="font-size:12px;margin-top:6px">[% "summary" %]</div><div style="font-size:11px;margin-top:6px"><a href="[% &quot;wikivoyage_url&quot; %]">de.wikivoyage.org</a></div></div>]]></mapTip>
</qgis>
