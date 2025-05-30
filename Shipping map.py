import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import Search
from branca.element import Element, MacroElement
from jinja2 import Template

# ✅ 文件路径
geojson_path = "/Users/zhengzhang/Desktop/Adelaide city/Suburbs_geojson/Suburbs_GDA2020.geojson"
csv_path = "/Users/zhengzhang/Desktop/Adelaide city/Shipping_policy/Shipping_Policy_Based_on_New_Ranges.csv"
output_path = "/Users/zhengzhang/Desktop/adelaide_map_with_color_edit.html"


# ✅ 数据读取与合并
gdf = gpd.read_file(geojson_path)
df = pd.read_csv(csv_path)
gdf["postcode"] = gdf["postcode"].astype(str)
df["postcode"] = df["postcode"].astype(str)
gdf = gdf[["suburb", "postcode", "geometry"]]
merged = gdf.merge(df, on=["suburb", "postcode"], how="left")
merged["search_key"] = merged["suburb"] + " " + merged["postcode"]
merged["fill_color"] = "#dddddd"  # 初始色

# 所有字段转为字符串
for col in merged.columns:
    if col != "geometry":
        merged[col] = merged[col].astype(str)

# ✅ 初始化地图
m = folium.Map(location=[-34.93, 138.6], zoom_start=12)

geojson = folium.GeoJson(
    merged,
    name="Suburbs",
    style_function=lambda feature: {
        "fillColor": feature["properties"]["fill_color"],
        "color": "black",
        "weight": 1.5,
        "fillOpacity": 0.6,
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["suburb", "postcode", "Distance_to_32WrightCt_km"],
        aliases=["Suburb", "Postcode", "Distance (km)"],
        sticky=True
    )
)
geojson.add_to(m)

# ✅ 添加搜索栏
Search(
    layer=geojson,
    search_label="search_key",
    placeholder="Search suburb/postcode",
    collapsed=False,
).add_to(m)

# ✅ 绑定 geojsonLayer 到 JS 全局
class BindGeoJson(MacroElement):
    def __init__(self, layer_name):
        super().__init__()
        self._template = Template(f"""
            <script>
                window.geojsonLayer = {{% raw %}}{layer_name}{{% endraw %}};
            </script>
        """)

m.get_root().add_child(BindGeoJson(geojson.get_name()))

# ✅ 注入调色板 + JS 交互
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
    width: 200px;
}}
.color-button {{
    width: 25px;
    height: 25px;
    border-radius: 50%;
    border: 2px solid gray;
    margin: 2px 0;
    display: inline-block;
    cursor: pointer;
}}
.color-button.active {{
    border: 3px solid black;
}}
#saveColorsBtn, #undoColorBtn {{
    display: block;
    margin-top: 8px;
    background: #007bff;
    color: white;
    padding: 4px 8px;
    border: none;
    border-radius: 4px;
    cursor: pointer;
}}
#undoColorBtn {{
    background: #dc3545;
}}
</style>

<div id="colorPalette">
  <strong>🎨 选择专区颜色</strong><br>
  <div id="colorButtons" style="display: flex; flex-direction: column; gap: 5px;"></div>
  <button id="saveColorsBtn">💾 保存</button>
  <button id="undoColorBtn">🧹 撤回</button>
</div>

<script>
const colorOptions = ["#2ca02c", "#ffcc00", "#ff7f0e", "#d62728", "#9467bd"];
const colorToZone = {{
    "#2ca02c": "专区 1",
    "#ffcc00": "专区 2",
    "#ff7f0e": "专区 3",
    "#d62728": "专区 4",
    "#9467bd": "专区 5"
}};
let selectedColor = colorOptions[0];
let colorMap = JSON.parse(localStorage.getItem("suburbColorMap") || "{{}}");
let undoStack = [];

function createColorButtons() {{
    const container = document.getElementById("colorButtons");
    container.innerHTML = "";
    colorOptions.forEach(color => {{
        const wrapper = document.createElement("div");
        wrapper.style.display = "flex";
        wrapper.style.alignItems = "center";
        wrapper.style.gap = "8px";

        const btn = document.createElement("div");
        btn.className = "color-button";
        btn.style.backgroundColor = color;
        btn.onclick = () => {{
            selectedColor = color;
            document.querySelectorAll(".color-button").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
        }};

        const label = document.createElement("span");
        label.textContent = colorToZone[color];

        wrapper.appendChild(btn);
        wrapper.appendChild(label);
        container.appendChild(wrapper);
    }});
    container.querySelector(".color-button").classList.add("active");
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
            undoStack.push({{ id: id, shape: shape }});  // 👈 保存撤回目标

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
        alert("✅ 区域颜色已保存！");
    }};

    document.getElementById("undoColorBtn").onclick = () => {{
        if (undoStack.length > 0) {{
            const last = undoStack.pop();
            last.shape.setStyle({{ fillColor: "#dddddd" }});  // 👈 重置为灰色
            delete colorMap[last.id];                         // 👈 从配色记录中移除
            last.shape.unbindTooltip();
        }} else {{
            alert("⚠️ 没有可以撤回的操作");
        }}
    }};
}});
</script>
"""

m.get_root().html.add_child(Element(js_css))
m.save(output_path)

print(f"✅ 地图已保存：{output_path}")
