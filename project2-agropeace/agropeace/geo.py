"""Pure-Python GIS primitives (WGS84 lon/lat).

No GDAL, GEOS or PostGIS is needed, so the system installs on any laptop a
state emergency agency or NGO already has. At state scale (tens of km) the
equirectangular approximation used for point-to-segment distance is accurate
to well under 1%.
"""

import math

EARTH_R_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_R_KM * math.asin(math.sqrt(a))


def bearing_deg(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


def compass(bearing: float) -> str:
    return ["N", "NE", "E", "SE", "S", "SW", "W", "NW"][int((bearing + 22.5) // 45) % 8]


def destination(lat, lon, bearing, dist_km):
    """Point reached travelling dist_km from (lat, lon) on the given bearing."""
    d = dist_km / EARTH_R_KM
    b = math.radians(bearing)
    p1, l1 = math.radians(lat), math.radians(lon)
    p2 = math.asin(math.sin(p1) * math.cos(d) + math.cos(p1) * math.sin(d) * math.cos(b))
    l2 = l1 + math.atan2(math.sin(b) * math.sin(d) * math.cos(p1), math.cos(d) - math.sin(p1) * math.sin(p2))
    return math.degrees(p2), math.degrees(l2)


def point_in_ring(lat, lon, ring) -> bool:
    """Ray casting. ring = [[lon, lat], ...] (GeoJSON order)."""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i]
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat):
            x_cross = (xj - xi) * (lat - yi) / (yj - yi) + xi
            if lon < x_cross:
                inside = not inside
        j = i
    return inside


def point_in_polygon(lat, lon, coords) -> bool:
    """coords = GeoJSON Polygon coordinates: [outer_ring, hole1, ...]."""
    if not point_in_ring(lat, lon, coords[0]):
        return False
    return not any(point_in_ring(lat, lon, hole) for hole in coords[1:])


def _local_xy(lat0, lat, lon):
    k = math.cos(math.radians(lat0))
    return math.radians(lon) * k * EARTH_R_KM, math.radians(lat) * EARTH_R_KM


def dist_point_segment_km(lat, lon, a, b) -> float:
    """a, b = [lon, lat]."""
    px, py = _local_xy(lat, lat, lon)
    ax, ay = _local_xy(lat, a[1], a[0])
    bx, by = _local_xy(lat, b[1], b[0])
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def dist_point_line_km(lat, lon, line) -> float:
    return min(dist_point_segment_km(lat, lon, line[i], line[i + 1]) for i in range(len(line) - 1))


def dist_point_polygon_km(lat, lon, coords) -> float:
    """0 inside, otherwise distance to the nearest edge."""
    if point_in_polygon(lat, lon, coords):
        return 0.0
    return min(dist_point_line_km(lat, lon, ring) for ring in coords)


def centroid(ring):
    """Area-weighted centroid of a ring, returned as (lat, lon)."""
    a = cx = cy = 0.0
    for i in range(len(ring) - 1):
        x0, y0 = ring[i]
        x1, y1 = ring[i + 1]
        f = x0 * y1 - x1 * y0
        a += f
        cx += (x0 + x1) * f
        cy += (y0 + y1) * f
    if abs(a) < 1e-12:
        xs, ys = zip(*ring)
        return sum(ys) / len(ys), sum(xs) / len(xs)
    a *= 0.5
    return cy / (6 * a), cx / (6 * a)


def ring_area_km2(ring) -> float:
    lat0 = sum(p[1] for p in ring) / len(ring)
    pts = [_local_xy(lat0, p[1], p[0]) for p in ring]
    return abs(sum(pts[i][0] * pts[i + 1][1] - pts[i + 1][0] * pts[i][1] for i in range(len(pts) - 1))) / 2


def grid_cells(bbox, cell_deg):
    """Yield (row, col, lat_center, lon_center, [s, w, n, e]) over bbox = [s, w, n, e]."""
    s, w, n, e = bbox
    rows = int(math.ceil((n - s) / cell_deg))
    cols = int(math.ceil((e - w) / cell_deg))
    for r in range(rows):
        for c in range(cols):
            cs, cw = s + r * cell_deg, w + c * cell_deg
            yield r, c, cs + cell_deg / 2, cw + cell_deg / 2, [cs, cw, cs + cell_deg, cw + cell_deg]


def snap_to_grid(lat, lon, cell_deg) -> tuple[float, float]:
    """Coarsen a location to the centre of its grid cell (location privacy)."""
    return (math.floor(lat / cell_deg) + 0.5) * cell_deg, (math.floor(lon / cell_deg) + 0.5) * cell_deg
