import geopandas as gpd
import folium
import numpy as np

# =========================
# 1. 파일 읽기
# =========================

nodes = gpd.read_file(
    "nodes_with_shade.geojson"
)

edges = gpd.read_file(
    "sujiku_edges_5186.geojson"
)

# =========================
# 2. 결측값 처리
# =========================

nodes["felt_temp"] = (
    nodes["felt_temp"]
    .fillna(nodes["felt_temp"].mean())
)

nodes["heat_grade"] = (
    nodes["heat_grade"]
    .fillna(nodes["heat_grade"].mean())
)

nodes["shade"] = (
    nodes["shade"]
    .fillna(0.2)
)

# =========================
# 3. 정규화 함수
# =========================

def normalize(series):

    min_val = series.min()
    max_val = series.max()

    return (
        (series - min_val)
        /
        (max_val - min_val)
    )

# =========================
# 4. 정규화
# =========================

nodes["felt_norm"] = normalize(
    nodes["felt_temp"]
)

nodes["grade_norm"] = normalize(
    nodes["heat_grade"]
)

# =========================
# 5. Heat Score 계산
# =========================
# 낮을수록 시원
# 높을수록 위험

nodes["heat_score"] = (
    0.7 * nodes["felt_norm"]
    +
    0.5 * nodes["grade_norm"]
    -
    0.8 * nodes["shade"]
)

# 보기 좋게
nodes["heat_score"] = (
    nodes["heat_score"]
    .round(3)
)

# =========================
# 6. 노드 score dictionary
# =========================

score_dict = dict(
    zip(
        nodes["osmid"],
        nodes["heat_score"]
    )
)

# =========================
# 7. 엣지 score 계산
# =========================

edge_scores = []

for _, edge in edges.iterrows():

    u = edge["u"]
    v = edge["v"]

    score_u = score_dict.get(u, np.nan)
    score_v = score_dict.get(v, np.nan)

    # 양 끝 노드 평균
    edge_score = np.nanmean(
        [score_u, score_v]
    )

    edge_scores.append(edge_score)

edges["heat_score"] = edge_scores

# =========================
# 8. score 범위 확인
# =========================

print()
print("===== SCORE 통계 =====")

print(
    edges["heat_score"].describe()
)

print()

print(
    "최소:",
    edges["heat_score"].min()
)

print(
    "최대:",
    edges["heat_score"].max()
)

# =========================
# 9. 웹 지도용 변환
# =========================

edges = edges.to_crs(epsg=4326)

# =========================
# 10. 지도 생성
# =========================

m = folium.Map(
    location=[37.32, 127.09],
    zoom_start=13,
    tiles="CartoDB positron"
)

# =========================
# 11. score 분위수 계산
# =========================
# 자동 색상 분포용

q1 = edges["heat_score"].quantile(0.33)
q2 = edges["heat_score"].quantile(0.66)

print()
print("Q1 =", q1)
print("Q2 =", q2)

# =========================
# 12. 도로 색칠
# =========================

for _, row in edges.iterrows():

    score = row["heat_score"]

    # ---------------------
    # 색상 결정
    # ---------------------

    if score <= q1:
        color = "blue"

    elif score <= q2:
        color = "orange"

    else:
        color = "red"

    # ---------------------
    # geometry 추출
    # ---------------------

    geom = row.geometry

    # MultiLineString 방지
    if geom.geom_type == "LineString":

        coords = [
            [y, x]
            for x, y in geom.coords
        ]

        folium.PolyLine(
            locations=coords,
            color=color,
            weight=3,
            opacity=0.8,
            tooltip=f"Heat Score: {score}"
        ).add_to(m)

# =========================
# 13. 저장
# =========================

m.save("heat_road_map.html")

print()
print("완료!")
print("heat_road_map.html 생성됨")