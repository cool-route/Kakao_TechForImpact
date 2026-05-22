from pathlib import Path

import geopandas as gpd
import folium
import numpy as np
import pandas as pd

# =========================================
# 0. 경로 설정
# =========================================

BASE_DIR = Path(__file__).resolve().parent

nodes_path = BASE_DIR / "data" / "nodes_with_score.geojson"
edges_path = BASE_DIR / "data" / "sujiku_edges_5186.geojson"
shelter_path = BASE_DIR / "data" / "shelters.geojson"

# =========================================
# 1. 파일 읽기
# =========================================

nodes = gpd.read_file(nodes_path)

edges = gpd.read_file(edges_path)

shelters = gpd.read_file(shelter_path)

# =========================================
# 2. 좌표계 변환
# Folium은 EPSG:4326 사용
# =========================================

nodes = nodes.to_crs(epsg=4326)

edges = edges.to_crs(epsg=4326)

shelters = shelters.to_crs(epsg=4326)

# =========================================
# 3. 노드 score 딕셔너리 생성
# =========================================

score_map = dict(
    zip(
        nodes["osmid"],
        nodes["heat_score"]
    )
)

# =========================================
# 4. edge score 계산
# 양 끝 노드 평균
# =========================================

edge_scores = []

for idx, edge in edges.iterrows():

    try:
        u = edge["u"]
        v = edge["v"]

        score_u = score_map.get(u, np.nan)
        score_v = score_map.get(v, np.nan)

        score = np.nanmean(
            [score_u, score_v]
        )

    except:
        score = np.nan

    edge_scores.append(score)

edges["heat_score"] = edge_scores

# =========================================
# 5. 결측 제거
# =========================================

edges = edges.dropna(
    subset=["heat_score"]
)

# =========================================
# 6. 분위수 계산
# 5단계 색상 분리
# =========================================

q1 = edges["heat_score"].quantile(0.2)
q2 = edges["heat_score"].quantile(0.4)
q3 = edges["heat_score"].quantile(0.6)
q4 = edges["heat_score"].quantile(0.8)

print()
print("===== Heat Score 분위수 =====")
print("Q1 =", q1)
print("Q2 =", q2)
print("Q3 =", q3)
print("Q4 =", q4)

# =========================================
# 7. 지도 생성
# =========================================

m = folium.Map(
    location=[37.32, 127.09],
    zoom_start=13
)

# =========================================
# 8. 색상 함수
# =========================================

def get_color(score):

    # 매우 시원
    if score <= q1:
        return "blue"

    # 시원
    elif score <= q2:
        return "green"

    # 보통
    elif score <= q3:
        return "yellow"

    # 더움
    elif score <= q4:
        return "orange"

    # 매우 더움
    else:
        return "red"

# =========================================
# 9. 도로 시각화
# =========================================

for idx, row in edges.iterrows():

    geom = row.geometry
    score = row["heat_score"]

    color = get_color(score)

    if geom.geom_type == "LineString":

        coords = [
            [y, x]
            for x, y in geom.coords
        ]

        folium.PolyLine(
            locations=coords,
            color=color,
            weight=4,
            opacity=0.9,
            tooltip=(
                f"Heat Score: {score:.2f}"
            )
        ).add_to(m)

# =========================================
# 10. 쉼터 마커 추가
# =========================================

for idx, row in shelters.iterrows():

    point = row.geometry

    if point is None:
        continue

    popup_text = f"""
    <b>쉼터명:</b> {row.get('name', '정보없음')}<br>
    <b>주소:</b> {row.get('address', '정보없음')}<br>
    <b>유형:</b> {row.get('type', '정보없음')}
    """

    folium.CircleMarker(
        location=[
            point.y,
            point.x
        ],
        radius=6,
        color="purple",
        fill=True,
        fill_opacity=0.9,
        popup=popup_text,
        tooltip=row.get(
            "name",
            "쉼터"
        )
    ).add_to(m)

# =========================================
# 11. 범례 추가
# =========================================

legend_html = """
<div style="
position: fixed;
bottom: 50px;
left: 50px;
width: 220px;
height: 260px;
background-color: white;
border:2px solid grey;
z-index:9999;
font-size:14px;
padding: 10px;
">

<b>Heat Score 단계</b><br><br>

<span style="color:blue;">■</span>
매우 시원<br><br>

<span style="color:green;">■</span>
시원<br><br>

<span style="color:gold;">■</span>
보통<br><br>

<span style="color:orange;">■</span>
더움<br><br>

<span style="color:red;">■</span>
매우 더움<br><br>

<span style="color:purple;">●</span>
무더위 쉼터

</div>
"""

m.get_root().html.add_child(
    folium.Element(legend_html)
)

# =========================================
# 12. 저장
# =========================================

output_path = BASE_DIR / "heat_score_map_5level.html"

m.save(output_path)

print()
print("완료!")
print(
    "heat_score_map_5level.html 생성됨"
)