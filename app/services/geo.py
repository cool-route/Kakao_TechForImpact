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
