<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<!-- Eisenbahn-Signatur im Stil der amtlichen Topokarten (DTK10/DTK100):
     schwarze Volllinie als "Gleis", darüber weiße Sprossen als "Schwellen".
     Umgesetzt als schwarze Basislinie + weiße, gestrichelte Decklinie. -->
<qgis version="3.34.0" styleCategories="Symbology">
  <renderer-v2 type="singleSymbol" symbollevels="1">
    <symbols>
      <symbol name="0" type="line" alpha="1" clip_to_extent="1" force_rhr="0">
        <!-- Layer 1: schwarzes Gleisband -->
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
        <!-- Layer 2: weiße Schwellen-Sprossen (gestrichelte Decklinie) -->
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
</qgis>
