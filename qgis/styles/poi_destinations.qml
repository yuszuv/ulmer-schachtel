<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!--
  Style für: poi_destinations (Punkt-Layer)
  Generiert von: qgis/styles/build_marker_styles.py
  Nicht manuell bearbeiten — Änderungen werden beim nächsten Generieren
  überschrieben. Stattdessen build_marker_styles.py anpassen, dann neu ausführen.
-->
<qgis version="3.34.0" styleCategories="Symbology|Labeling|MapTips">
  <!-- Renderer: RuleRenderer — eine Regel je POI-Kategorie.
       Jede Regel wählt ihr Icon über symbol="…", filtert per filter="…" auf das
       Attribut "category" und blendet sich maßstabsabhängig ein:
       scalemaxdenom = größter (am weitesten herausgezoomter) Maßstabsnenner, ab
       dem die Regel sichtbar wird. So erscheinen wichtige POIs früher als
       sekundäre:
         dracula_city, city → ab 1:6 000 000
         danube_delta       → ab 1:3 000 000
       Im Unterschied zu categorizedSymbol (nur Icon-Wahl) erlaubt RuleRenderer
       zusätzlich diese Maßstabs-Staffelung pro Kategorie. -->
  <renderer-v2 type="RuleRenderer" symbollevels="0">
    <rules key="{poi-rules}">
      <rule symbol="0" filter="&quot;category&quot; = 'dracula_city'" scalemaxdenom="6000000" label="Dracula-Stadt" key="{poi-rule-dracula_city}"/>
      <rule symbol="1" filter="&quot;category&quot; = 'city'" scalemaxdenom="6000000" label="Stadt" key="{poi-rule-city}"/>
      <rule symbol="2" filter="&quot;category&quot; = 'danube_delta'" scalemaxdenom="3000000" label="Donaudelta" key="{poi-rule-danube_delta}"/>
    </rules>
    <symbols>
      <symbol name="0" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- SvgMarker: SVG-Icon als Marker, Base64-direkt eingebettet — kein Dateipfad,
             daher in QField ohne lokale Ordnerstruktur verwendbar.
             name="base64:…" = SVG-Inhalt als Data-URI statt Pfadangabe.
             size_unit="MM" = gerätunabhängige Millimeter (nicht Pixel).
             scale_method="diameter" = Größe ist der Durchmesser, nicht der Radius.
             anchor_point="1" = Marker-Mittelpunkt als Ankerpunkt
               (0 = oben/links, 1 = Mitte, 2 = unten/rechts). -->
        <layer class="SvgMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPCEtLSBEcmFjdWxhLVN0YWR0OiBCdXJnICsgRmxlZGVybWF1cyBhdWYgZHVua2Vscm90ZW0gQmFkZ2UgLS0+CjxzdmcgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB2aWV3Qm94PSIwIDAgNjQgNjQiIHdpZHRoPSI2NCIgaGVpZ2h0PSI2NCI+CiAgPGNpcmNsZSBjeD0iMzIiIGN5PSIzMiIgcj0iMzAiIGZpbGw9IiM3ZTI0MjIiIHN0cm9rZT0iIzNhMTExMCIgc3Ryb2tlLXdpZHRoPSIyIi8+CiAgPCEtLSBUw7xybWUgKyBNYXVlciAtLT4KICA8ZyBmaWxsPSIjZjRlY2UxIj4KICAgIDxyZWN0IHg9IjE1IiB5PSIyNyIgd2lkdGg9IjkiIGhlaWdodD0iMjIiLz4KICAgIDxyZWN0IHg9IjQwIiB5PSIyNyIgd2lkdGg9IjkiIGhlaWdodD0iMjIiLz4KICAgIDxyZWN0IHg9IjIyIiB5PSIzMyIgd2lkdGg9IjIwIiBoZWlnaHQ9IjE2Ii8+CiAgICA8IS0tIFppbm5lbiAtLT4KICAgIDxyZWN0IHg9IjE1IiB5PSIyNCIgd2lkdGg9IjIuNiIgaGVpZ2h0PSI0Ii8+CiAgICA8cmVjdCB4PSIxOC43IiB5PSIyNCIgd2lkdGg9IjIuNiIgaGVpZ2h0PSI0Ii8+CiAgICA8cmVjdCB4PSIyMi40IiB5PSIyNCIgd2lkdGg9IjIuNiIgaGVpZ2h0PSI0Ii8+CiAgICA8cmVjdCB4PSI0MCIgeT0iMjQiIHdpZHRoPSIyLjYiIGhlaWdodD0iNCIvPgogICAgPHJlY3QgeD0iNDMuNyIgeT0iMjQiIHdpZHRoPSIyLjYiIGhlaWdodD0iNCIvPgogICAgPHJlY3QgeD0iNDcuNCIgeT0iMjQiIHdpZHRoPSIyLjYiIGhlaWdodD0iNCIvPgogICAgPHJlY3QgeD0iMjQiIHk9IjMwIiB3aWR0aD0iMi42IiBoZWlnaHQ9IjQiLz4KICAgIDxyZWN0IHg9IjMwLjciIHk9IjMwIiB3aWR0aD0iMi42IiBoZWlnaHQ9IjQiLz4KICAgIDxyZWN0IHg9IjM3LjQiIHk9IjMwIiB3aWR0aD0iMi42IiBoZWlnaHQ9IjQiLz4KICA8L2c+CiAgPCEtLSBUb3IgLS0+CiAgPHBhdGggZD0iTTI5IDQ5IHYtNiBhMyAzIDAgMCAxIDYgMCB2NiB6IiBmaWxsPSIjM2ExMTEwIi8+CiAgPCEtLSBGbGVkZXJtYXVzIC0tPgogIDxwYXRoIGQ9Ik0zMiAxMyBjMiAwIDIuNCAyIDQgMiBjMS42IDAgMi0xLjQgMy42LTEgYy0xIDEuMi0xIDIuNC0zIDIuOAogICAgICAgICAgIGMtMS44IC40LTIuNi0xLTQuNi0xIGMtMiAwLTIuOCAxLjQtNC42IDEgYy0yLS40LTItMS42LTMtMi44CiAgICAgICAgICAgYzEuNi0uNCAyIDEgMy42IDEgYzEuNiAwIDItMiA0LTIgeiIgZmlsbD0iI2Y0ZWNlMSIvPgo8L3N2Zz4K"/>
            <Option name="size" type="QString" value="7.5"/>
            <Option name="size_unit" type="QString" value="MM"/>
            <Option name="angle" type="QString" value="0"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="fixedAspectRatio" type="QString" value="0"/>
            <Option name="scale_method" type="QString" value="diameter"/>
            <Option name="vertical_anchor_point" type="QString" value="1"/>
            <Option name="horizontal_anchor_point" type="QString" value="1"/>
          </Option>
        </layer>
      </symbol>
      <symbol name="1" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- SvgMarker: SVG-Icon als Marker, Base64-direkt eingebettet — kein Dateipfad,
             daher in QField ohne lokale Ordnerstruktur verwendbar.
             name="base64:…" = SVG-Inhalt als Data-URI statt Pfadangabe.
             size_unit="MM" = gerätunabhängige Millimeter (nicht Pixel).
             scale_method="diameter" = Größe ist der Durchmesser, nicht der Radius.
             anchor_point="1" = Marker-Mittelpunkt als Ankerpunkt
               (0 = oben/links, 1 = Mitte, 2 = unten/rechts). -->
        <layer class="SvgMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPCEtLSBTdGFkdDogU2t5bGluZSBhdWYgYmVybnN0ZWluZmFyYmVuZW0gQmFkZ2UgLS0+CjxzdmcgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIiB2aWV3Qm94PSIwIDAgNjQgNjQiIHdpZHRoPSI2NCIgaGVpZ2h0PSI2NCI+CiAgPGNpcmNsZSBjeD0iMzIiIGN5PSIzMiIgcj0iMzAiIGZpbGw9IiNiNTY1MWQiIHN0cm9rZT0iIzVlMzQxMCIgc3Ryb2tlLXdpZHRoPSIyIi8+CiAgPGcgZmlsbD0iI2Y3ZWZlMiI+CiAgICA8cmVjdCB4PSIxNSIgeT0iMzQiIHdpZHRoPSIxMCIgaGVpZ2h0PSIxNiIvPgogICAgPHJlY3QgeD0iMjciIHk9IjIyIiB3aWR0aD0iMTEiIGhlaWdodD0iMjgiLz4KICAgIDxyZWN0IHg9IjQwIiB5PSIyOSIgd2lkdGg9IjEwIiBoZWlnaHQ9IjIxIi8+CiAgPC9nPgogIDwhLS0gRmVuc3RlciAtLT4KICA8ZyBmaWxsPSIjYjU2NTFkIj4KICAgIDxyZWN0IHg9IjE4IiB5PSIzNyIgd2lkdGg9IjIiIGhlaWdodD0iMiIvPjxyZWN0IHg9IjIyIiB5PSIzNyIgd2lkdGg9IjIiIGhlaWdodD0iMiIvPgogICAgPHJlY3QgeD0iMTgiIHk9IjQyIiB3aWR0aD0iMiIgaGVpZ2h0PSIyIi8+PHJlY3QgeD0iMjIiIHk9IjQyIiB3aWR0aD0iMiIgaGVpZ2h0PSIyIi8+CiAgICA8cmVjdCB4PSIzMCIgeT0iMjYiIHdpZHRoPSIyIiBoZWlnaHQ9IjIiLz48cmVjdCB4PSIzNCIgeT0iMjYiIHdpZHRoPSIyIiBoZWlnaHQ9IjIiLz4KICAgIDxyZWN0IHg9IjMwIiB5PSIzMSIgd2lkdGg9IjIiIGhlaWdodD0iMiIvPjxyZWN0IHg9IjM0IiB5PSIzMSIgd2lkdGg9IjIiIGhlaWdodD0iMiIvPgogICAgPHJlY3QgeD0iMzAiIHk9IjM2IiB3aWR0aD0iMiIgaGVpZ2h0PSIyIi8+PHJlY3QgeD0iMzQiIHk9IjM2IiB3aWR0aD0iMiIgaGVpZ2h0PSIyIi8+CiAgICA8cmVjdCB4PSIzMCIgeT0iNDEiIHdpZHRoPSIyIiBoZWlnaHQ9IjIiLz48cmVjdCB4PSIzNCIgeT0iNDEiIHdpZHRoPSIyIiBoZWlnaHQ9IjIiLz4KICAgIDxyZWN0IHg9IjQzIiB5PSIzMyIgd2lkdGg9IjIiIGhlaWdodD0iMiIvPjxyZWN0IHg9IjQ3IiB5PSIzMyIgd2lkdGg9IjIiIGhlaWdodD0iMiIvPgogICAgPHJlY3QgeD0iNDMiIHk9IjM4IiB3aWR0aD0iMiIgaGVpZ2h0PSIyIi8+PHJlY3QgeD0iNDciIHk9IjM4IiB3aWR0aD0iMiIgaGVpZ2h0PSIyIi8+CiAgPC9nPgo8L3N2Zz4K"/>
            <Option name="size" type="QString" value="7.0"/>
            <Option name="size_unit" type="QString" value="MM"/>
            <Option name="angle" type="QString" value="0"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="fixedAspectRatio" type="QString" value="0"/>
            <Option name="scale_method" type="QString" value="diameter"/>
            <Option name="vertical_anchor_point" type="QString" value="1"/>
            <Option name="horizontal_anchor_point" type="QString" value="1"/>
          </Option>
        </layer>
      </symbol>
      <symbol name="2" type="marker" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- SvgMarker: SVG-Icon als Marker, Base64-direkt eingebettet — kein Dateipfad,
             daher in QField ohne lokale Ordnerstruktur verwendbar.
             name="base64:…" = SVG-Inhalt als Data-URI statt Pfadangabe.
             size_unit="MM" = gerätunabhängige Millimeter (nicht Pixel).
             scale_method="diameter" = Größe ist der Durchmesser, nicht der Radius.
             anchor_point="1" = Marker-Mittelpunkt als Ankerpunkt
               (0 = oben/links, 1 = Mitte, 2 = unten/rechts). -->
        <layer class="SvgMarker" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="name" type="QString" value="base64:PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iVVRGLTgiPz4KPCEtLSBEb25hdWRlbHRhOiBmbGllZ2VuZGVyIFZvZ2VsIMO8YmVyIFNjaGlsZi9XYXNzZXIgYXVmIHBldHJvbGZhcmJlbmVtIEJhZGdlIC0tPgo8c3ZnIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgdmlld0JveD0iMCAwIDY0IDY0IiB3aWR0aD0iNjQiIGhlaWdodD0iNjQiPgogIDxjaXJjbGUgY3g9IjMyIiBjeT0iMzIiIHI9IjMwIiBmaWxsPSIjMmY3ZDZiIiBzdHJva2U9IiMxMzM5MmYiIHN0cm9rZS13aWR0aD0iMiIvPgogIDwhLS0gVm9nZWwgKE3DtndlKSAtLT4KICA8cGF0aCBkPSJNMTYgMjggUTI2IDE4IDMyIDI3IFEzOCAxOCA0OCAyOCIKICAgICAgICBmaWxsPSJub25lIiBzdHJva2U9IiNmMmY3ZjQiIHN0cm9rZS13aWR0aD0iMy40IgogICAgICAgIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgc3Ryb2tlLWxpbmVqb2luPSJyb3VuZCIvPgogIDwhLS0gV2Fzc2VybGluaWVuIC0tPgogIDxnIHN0cm9rZT0iI2YyZjdmNCIgc3Ryb2tlLXdpZHRoPSIyLjQiIHN0cm9rZS1saW5lY2FwPSJyb3VuZCIgb3BhY2l0eT0iMC45NSI+CiAgICA8cGF0aCBkPSJNMTYgNDQgcTQgLTMgOCAwIHE0IDMgOCAwIHE0IC0zIDggMCBxNCAzIDggMCIgZmlsbD0ibm9uZSIvPgogIDwvZz4KICA8IS0tIFNjaGlsZiAtLT4KICA8ZyBmaWxsPSIjZjJmN2Y0Ij4KICAgIDxyZWN0IHg9IjI0IiB5PSIzNiIgd2lkdGg9IjEuOCIgaGVpZ2h0PSI5IiByeD0iMC45Ii8+CiAgICA8cGF0aCBkPSJNMjQuOSAzNCBxMyAxIDEgNCBxLTIgLTEgLTEgLTR6Ii8+CiAgICA8cmVjdCB4PSIzOCIgeT0iMzUiIHdpZHRoPSIxLjgiIGhlaWdodD0iMTAiIHJ4PSIwLjkiLz4KICAgIDxwYXRoIGQ9Ik0zOC45IDMzIHEzIDEgMSA0IHEtMiAtMSAtMSAtNHoiLz4KICA8L2c+Cjwvc3ZnPgo="/>
            <Option name="size" type="QString" value="7.0"/>
            <Option name="size_unit" type="QString" value="MM"/>
            <Option name="angle" type="QString" value="0"/>
            <Option name="offset" type="QString" value="0,0"/>
            <Option name="offset_unit" type="QString" value="MM"/>
            <Option name="fixedAspectRatio" type="QString" value="0"/>
            <Option name="scale_method" type="QString" value="diameter"/>
            <Option name="vertical_anchor_point" type="QString" value="1"/>
            <Option name="horizontal_anchor_point" type="QString" value="1"/>
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
                  fontFamily="Sans Serif" fontSize="8" fontSizeUnit="Point"
                  fontWeight="75" namedStyle="Bold" fontItalic="0"
                  fontUnderline="0" fontStrikeout="0" fontKerning="1"
                  fontLetterSpacing="0" fontWordSpacing="0"
                  textColor="107,79,42,255" textOpacity="1" blendMode="0"
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
                 scaleVisibility="1" scaleMin="0" scaleMax="3000000"
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
  <mapTip><![CDATA[<div style="font-family:serif;color:#39312b;max-width:260px"><div style="font-size:14px;font-weight:bold;color:#6b4f2a">[% "name" %]</div><div style="font-size:11px;color:#888;margin-top:2px">[% "category" %]&nbsp;·&nbsp;Prio&nbsp;[% "priority" %]</div><div style="font-size:12px;margin-top:6px">[% "notes" %]</div></div>]]></mapTip>
</qgis>
