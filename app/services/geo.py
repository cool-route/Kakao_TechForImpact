from math import asin, cos, radians, sin, sqrt


Coordinate = tuple[float, float]


def haversine_m(a: Coordinate, b: Coordinate) -> float:
    lat1, lng1 = a
    lat2, lng2 = b
    radius_m = 6_371_000
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    x = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 2 * radius_m * asin(sqrt(x))


def point_to_segment_distance_m(p: Coordinate, a: Coordinate, b: Coordinate) -> float:
    """점 p에서 선분 ab까지의 최소 거리 (미터). 짧은 거리 평면 근사."""
    if a == b:
        return haversine_m(p, a)

    lat_p, lng_p = p
    lat_a, lng_a = a
    lat_b, lng_b = b

    cos_lat = cos(radians((lat_a + lat_b) / 2))
    M = 111_000.0  # 위도 1도 = 약 111km

    ax = (lat_a - lat_p) * M
    ay = (lng_a - lng_p) * M * cos_lat
    bx = (lat_b - lat_p) * M
    by = (lng_b - lng_p) * M * cos_lat

    dx = bx - ax
    dy = by - ay
    seg_len_sq = dx * dx + dy * dy
    t = max(0.0, min(1.0, -(ax * dx + ay * dy) / seg_len_sq))

    closest_lat = lat_a + t * (lat_b - lat_a)
    closest_lng = lng_a + t * (lng_b - lng_a)
    return haversine_m(p, (closest_lat, closest_lng))
