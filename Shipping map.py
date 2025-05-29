import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import Search
from tqdm import tqdm

# ✅ 路径设置
geojson_path = "/Users/zhengzhang/Desktop/Adelaide city/Suburbs_geojson/Suburbs_GDA2020.geojson"
csv_path = "/Users/zhengzhang/Desktop/Adelaide city/Shipping_policy/Shipping_Policy_Based_on_New_Ranges.csv"

# ✅ 读取数据
gdf = gpd.read_file(geojson_path)
pricing_df = pd.read_csv(csv_path)

# ✅ 标准化字段
gdf = gdf[["postcode", "suburb", "geometry"]]
gdf["postcode"] = gdf["postcode"].astype(str)
pricing_df["postcode"] = pricing_df["postcode"].astype(str)

# ✅ 匹配距离范围
def assign_distance_range(km):
    try:
        km = float(km)
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
    except:
        return "Unknown"

pricing_df["Distance_Range"] = pricing_df["Distance_to_32WrightCt_km"].apply(assign_distance_range)

# ✅ 配送费用策略
pricing_df["Fee_If_Under"] = pricing_df["Distance_Range"].map({
    "≤ 5 km": "$6",
    "> 5 km 且 ≤ 10 km": "$6",
    "> 10 km 且 ≤ 15 km": "$8",
    "> 15 km 且 ≤ 20 km": "$10",
    "> 20 km": "$12"
}).fillna("N/A")

# ✅ 合并
merged_gdf = gdf.merge(pricing_df, on=["postcode", "suburb"], how="left")

# ✅ 加载进度条（模拟）
for _ in tqdm(range(100), desc="📍 构建地图数据"):
    pass

# ✅ 填色映射
color_map = {
    "≤ 5 km": "#2ca02c",                  # green
    "> 5 km 且 ≤ 10 km": "#ffcc00",       # yellow
    "> 10 km 且 ≤ 15 km": "#ff7f0e",      # orange
    "> 15 km 且 ≤ 20 km": "#d62728",      # red
    "> 20 km": "#9467bd"                  # purple
}
merged_gdf["fill_color"] = merged_gdf["Distance_Range"].map(color_map).fillna("#dddddd")

# ✅ 搜索字段（suburb + postcode）
merged_gdf["search_key"] = (merged_gdf["suburb"] + " " + merged_gdf["postcode"]).astype(str)

# ✅ 确保所有非几何列为字符串，避免 JSON 问题
non_geometry_cols = [col for col in merged_gdf.columns if col != "geometry"]
merged_gdf[non_geometry_cols] = merged_gdf[non_geometry_cols].astype(str)

# ✅ 创建地图
m = folium.Map(location=[-34.93, 138.6], zoom_start=12)

# ✅ GeoJSON 图层
geojson_layer = folium.GeoJson(
    merged_gdf,
    name="Adelaide Shipping Zones",
    style_function=lambda feature: {
        'fillColor': feature['properties']['fill_color'],
        'color': 'black',
        'weight': 1.2,
        'fillOpacity': 0.6
    },
    highlight_function=lambda feature: {
        'fillColor': '#ffff00',
        'color': 'blue',
        'weight': 2,
        'fillOpacity': 0.9
    },
    tooltip=folium.GeoJsonTooltip(
        fields=["postcode", "suburb", "Distance_to_32WrightCt_km", "Distance_Range", "Fee_If_Under"],
        aliases=["Postcode", "Suburb", "Distance (km)", "Range", "Delivery Fee"],
        sticky=True,
        opacity=0.9
    )
).add_to(m)

# ✅ 搜索插件（支持 postcode + suburb）
Search(
    layer=geojson_layer,
    search_label="search_key",
    placeholder="Search by suburb or postcode",
    collapsed=False,
).add_to(m)

# ✅ 输出地图
output_path = "/Users/zhengzhang/Desktop/adelaide_shipping_colored_map_with_search.html"
m.save(output_path)
print(f"✅ 地图已生成并保存至: {output_path}")
