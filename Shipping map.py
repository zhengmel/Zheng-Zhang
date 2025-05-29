import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import Search

# ✅ 本地路径
geojson_path = "/Users/zhengzhang/Desktop/Adelaide city/Suburbs_geojson/Suburbs_GDA2020.geojson"
csv_path = "/Users/zhengzhang/Desktop/Adelaide city/Shipping_policy/Shipping_Policy_Based_on_New_Ranges.csv"
output_path = "/Users/zhengzhang/Desktop/adelaide_map_with_color_edit.html"

# ✅ 读取数据
gdf = gpd.read_file(geojson_path)
df = pd.read_csv(csv_path)

# ✅ 清洗并合并
gdf = gdf[["suburb", "postcode", "geometry"]]
gdf["postcode"] = gdf["postcode"].astype(str)
df["postcode"] = df["postcode"].astype(str)
merged = gdf.merge(df, on=["suburb", "postcode"], how="left")
merged["search_key"] = merged["suburb"] + " " + merged["postcode"]

# ✅ 初始颜色：全部默认灰色
merged["fill_color"] = "#dddddd"
for col in merged.columns:
    if col != "geometry":
        merged[col] = merged[col].astype(str)

# ✅ 创建地图
m = folium.Map(location=[-34.93, 138.6], zoom_start=12)

# ✅ 添加 GeoJSON 图层
geojson = folium.GeoJson(
    merged,
    name="Suburbs",
    style_function=lambda feature: {
        'fillColor': feature['properties']['fill_color'],
        'color': "black",
        'weight': 1.5,
        'fillOpacity': 0.6
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["suburb", "postcode", "Distance_to_32WrightCt_km"],
        aliases=["Suburb", "Postcode", "Distance (km)"],
        sticky=True
    )
)
geojson.add_to(m)

# ✅ 搜索栏
Search(
    layer=geojson,
    search_label="search_key",
    placeholder="Search suburb/postcode",
    collapsed=False,
).add_to(m)

# ✅ 注入 JS + 样式
js_css = f"""
<style>
#colorPalette {{
    position: absolute;
    top: 160px;
    left: 10px;
    z-index: 9999;
    background: white;
    padding: 8px;
    border: 1px solid #999;
    border-radius: 8px;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.3);
    font-size: 14px;
    width: 180px;
}}
.color-button {{
    width: 25px;
    height: 25px;
    border-radius: 50%;
    border: 2px solid gray;
    margin: 3px;
    display: inline-block;
    cursor: pointer;
}}
.color-button.active {{
    border: 3px solid black;
}}
#saveColorsBtn {{
    display: block;
    margin-top: 10px;
    background: #007bff;
    color: white;
    padding: 4px 8px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}}
</style>

<div id="colorPalette">
  <strong>🎨 Choose Color</strong><br>
  <div id="colorButtons"></div>
  <button id="saveColorsBtn">💾 Save</button>
</div>

<script>
const colorOptions = ["#2ca02c", "#ffcc00", "#ff7f0e", "#d62728", "#9467bd"];
const colorToZone = {{
    "#2ca02c": "专区 1",  // green
    "#ffcc00": "专区 2",  // yellow
    "#ff7f0e": "专区 3",  // orange
    "#d62728": "专区 4",  // red
    "#9467bd": "专区 5"   // purple
}};
let selectedColor = colorOptions[0];
let colorMap = JSON.parse(localStorage.getItem("suburbColorMap") || "{{}}");

function createColorButtons() {{
    const container = document.getElementById("colorButtons");
    container.innerHTML = "";
    colorOptions.forEach(color => {{
        const btn = document.createElement("div");
        btn.className = "color-button";
        btn.style.backgroundColor = color;
        btn.onclick = () => {{
            selectedColor = color;
            document.querySelectorAll(".color-button").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
        }};
        container.appendChild(btn);
    }});
    container.firstChild.classList.add("active");
}}

function applyColoring(layer) {{
    for (let key in layer._layers) {{
        const shape = layer._layers[key];
        const props = shape.feature.properties;
        const id = props.suburb + "_" + props.postcode;

        if (colorMap[id]) {{
            shape.setStyle({{ fillColor: colorMap[id] }});
        }}

        shape.on("click", function() {{
            shape.setStyle({{ fillColor: selectedColor }});
            colorMap[id] = selectedColor;
            const zone = colorToZone[selectedColor] || "未定义";

            const html = `
              <b>Suburb:</b> ${{props.suburb}}<br>
              <b>Postcode:</b> ${{props.postcode}}<br>
              <b>Distance:</b> ${{props.Distance_to_32WrightCt_km}} km<br>
              <b>Zone:</b> ${{zone}}
            `;
            shape.unbindTooltip();
            shape.bindTooltip(html, {{sticky: true}}).openTooltip();
        }});
    }}
}}

document.addEventListener("DOMContentLoaded", () => {{
    createColorButtons();
    applyColoring({geojson.get_name()});
    document.getElementById("saveColorsBtn").onclick = () => {{
        localStorage.setItem("suburbColorMap", JSON.stringify(colorMap));
        alert("✅ Coloring saved locally!");
    }};
}});
</script>
"""

# ✅ 添加 JS + CSS 到地图
m.get_root().html.add_child(folium.Element(js_css))

# ✅ 保存 HTML 文件
m.save(output_path)
print(f"✅ 地图已生成：{output_path}")
