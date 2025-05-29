from tqdm import tqdm
import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import Search

# ✅ 路径配置
geojson_path = "/Users/zhengzhang/Desktop/Adelaide city/Suburbs_geojson/Suburbs_GDA2020.geojson"
csv_path = "/Users/zhengzhang/Desktop/Adelaide city/Shipping_policy/Shipping_Policy_Based_on_New_Ranges.csv"

# ✅ 读取数据（加上 tqdm 包裹模拟加载）
print("🔄 加载 GeoJSON 和 CSV 数据...")
gdf = gpd.read_file(geojson_path)
pricing_df = pd.read_csv(csv_path)

# ✅ 标准化字段
print("🛠️ 标准化字段...")
gdf = gdf[["postcode", "suburb", "geometry"]]
gdf["postcode"] = gdf["postcode"].astype(str).str.strip()
pricing_df["postcode"] = pricing_df["postcode"].astype(str).str.strip()

# ✅ 计算距离区间
print("📏 计算 Distance_Range 字段...")

def assign_distance_range(km):
    if km <= 5:
        return "≤ 5 km"
    elif km <= 10:
        return "> 5 km 且 ≤ 10 km"
    elif km <= 15:
        return "> 10 km 且 ≤ 15 km"
    elif km <= 20:
        return "> 15 km 且 ≤ 20 km"
    else:
        return "> 20 km"

pricing_df["Distance_to_32WrightCt_km"] = pricing_df["Distance_to_32WrightCt_km"].astype(float)

# 使用 tqdm 显示进度
tqdm.pandas(desc="🔍 分配配送范围")
pricing_df["Distance_Range"] = pricing_df["Distance_to_32WrightCt_km"].progress_apply(assign_distance_range)

# ✅ 分配配送费用
print("💸 生成配送费用字段...")
pricing_df["Fee_If_Under"] = pricing_df["Distance_Range"].map({
    "≤ 5 km": "$6",
    "> 5 km 且 ≤ 10 km": "$6",
    "> 10 km 且 ≤ 15 km": "$8",
    "> 15 km 且 ≤ 20 km": "$10",
    "> 20 km": "$12"
})

# ✅ 合并地图与定价信息
print("🔗 合并 GeoJSON 和价格数据...")
merged_gdf = gdf.merge(pricing_df, on=["postcode", "suburb"], how="left")

# ✅ 着色
print("🎨 分配颜色...")
color_map = {
    "≤ 5 km": "#2ca02c",
    "> 5 km 且 ≤ 10 km": "#ffcc00",
    "> 10 km 且 ≤ 15 km": "#ff7f0e",
    "> 15 km 且 ≤ 20 km": "#d62728",
    "> 20 km": "#9467bd"
}
merged_gdf["fill_color"] = merged_gdf["Distance_Range"].map(color_map).fillna("#dddddd")

# ✅ 字段类型转换避免 JSON 报错
print("🧼 清洗非几何字段为字符串...")
non_geometry_cols = [col for col in merged_gdf.columns if col != "geometry"]
merged_gdf[non_geometry_cols] = merged_gdf[non_geometry_cols].astype(str)

# ✅ 创建地图
print("🗺️ 创建地图...")
m = folium.Map(location=[-34.93, 138.6], zoom_start=12)

# ✅ 添加 GeoJson 图层
print("📌 加载图层和搜索功能...")
geojson_layer = folium.GeoJson(
    merged_gdf,
    name="Adelaide Shipping Zones",
    style_function=lambda feature: {
        'fillColor': feature['properties']['fill_color'],
        'color': 'black',
        'weight': 1.5,
        'fillOpacity': 0.6
    },
    highlight_function=lambda feature: {
        'fillColor': '#ffff00',
        'color': 'blue',
        'weight': 3,
        'fillOpacity': 0.9
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["postcode", "suburb", "Distance_Range", "Fee_If_Under"],
        aliases=["Postcode", "Suburb", "Distance", "Delivery Fee"],
        sticky=True,
        opacity=0.9
    )
).add_to(m)

# ✅ 添加搜索字段
merged_gdf["search_key"] = merged_gdf["suburb"] + " " + merged_gdf["postcode"]

# ✅ 添加搜索栏
Search(
    layer=geojson_layer,
    search_label='search_key',
    placeholder='Search suburb or postcode',
    collapsed=False,
).add_to(m)

# ✅ 导出地图
print("💾 导出 HTML 文件...")
m.save("adelaide_shipping_colored_map_with_search.html")
print("✅ 地图已生成并保存为 'adelaide_shipping_colored_map_with_search.html'")
