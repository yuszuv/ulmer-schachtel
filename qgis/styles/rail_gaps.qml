<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!-- Stil für: rail_gaps (Linien-Layer)
     Handgepflegt: diese Datei direkt bearbeiten (nicht generiert).

     Zeigt Streckenabschnitte an, für die keine Gleisgeometrie aus OSM
     geroutet werden konnte (Netzwerklücke). Die Linie läuft direkt zwischen
     den beiden Endbahnhöfen — zeigt also grob "wo die Strecke entlanggeht",
     ohne den exakten Verlauf zu kennen.

     Visuelles Konzept ("Ghost"):
       Gleicher Farbton wie rail_lines (Sepia #6b4f2a), aber:
       - nur 35 % Deckkraft → durchscheinend, gehört dazu aber ist klar
         als "unbekannt" lesbar
       - lange gestrichelt (10 mm Strich, 4 mm Lücke) statt der
         Schwellen-Optik der echten Strecke
       - keine zweite Lage (Schwellen) → bewusst reduziert
       - kein Label: der route_id-Code klebt schon an der Hauptlinie

     Ladeanweisung in QGIS:
       Layer Properties → Style → Load Style → "All Categories" wählen. -->
<qgis version="3.34.0" styleCategories="Symbology|Labeling">
  <!-- Renderer: singleSymbol — alle Lücken sehen gleich aus; die Zugehörigkeit
       zu einer Magistrale ist durch die räumliche Nähe zur Hauptlinie erkennbar,
       nicht durch Farbe. Ein kategorisierter Renderer nach route_id wäre
       aufwendiger und optisch unruhiger. -->
  <renderer-v2 type="singleSymbol" symbollevels="1">
    <symbols>
      <symbol name="0" type="line" alpha="0.35" clip_to_extent="1" force_rhr="0">
        <!-- Einzige Lage: gestrichelte Sepia-Linie.
             alpha="0.35" auf dem Symbol (nicht auf dem Layer) wirkt in QGIS
             konsistenter als die Layer-Transparenz-Einstellung.
             customdash "10;4" = 10 mm Strich, 4 mm Lücke — lange Striche
             signalisieren "ungefähre Linie", kurze Striche würden eher
             "unsicher" oder "in Planung" lesen. -->
        <layer class="SimpleLine" enabled="1" pass="0" locked="0">
          <Option type="Map">
            <Option name="line_color" type="QString" value="107,79,42,255"/>
            <Option name="line_width" type="QString" value="1.2"/>
            <Option name="line_width_unit" type="QString" value="Point"/>
            <Option name="line_style" type="QString" value="no"/>
            <Option name="use_custom_dash" type="QString" value="1"/>
            <Option name="customdash" type="QString" value="10;4"/>
            <Option name="customdash_unit" type="QString" value="MM"/>
            <Option name="capstyle" type="QString" value="round"/>
            <Option name="joinstyle" type="QString" value="round"/>
          </Option>
        </layer>
      </symbol>
    </symbols>
  </renderer-v2>
  <!-- Keine Beschriftung: route_id klebt bereits an der Hauptlinie (rail_lines).
       Eine zweite Beschriftung direkt daneben wäre visueller Lärm. -->
  <labeling type="simple">
    <settings calloutType="simple">
      <rendering drawLabels="0" displayAll="0" scaleVisibility="0"
                 scaleMin="1" scaleMax="10000000"/>
    </settings>
  </labeling>
</qgis>
