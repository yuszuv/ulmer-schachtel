"""Rail network graph and shortest-path routing — pure domain, no IO.

`RailNetwork` turns OpenStreetMap `railway=rail` ways into an undirected weighted
graph and routes a magistrală's station sequence along the actual tracks, so the
map lines follow the valleys instead of cutting straight across the Carpathians.

Pattern fit (see docs/07_architecture.md): there is no graph pattern in the
project, so this module deliberately mirrors the two it does have —

  * **Layering:** like `domain.py`, this is the *inner* layer: no IO, imports only
    `domain` (Coordinate) and `result` (Maybe). The network fetch stays in the
    `overpass.py` gateway; `ingest.py` orchestrates.
  * **`StationIndex` + Pattern 2 (Maybe):** `RailNetwork.from_overpass(data)`
    parallels `StationIndex.from_overpass(data)`, and `route()` returns
    `Maybe[list[Coordinate]]` — an unreachable pair is `Nothing` (a value), not an
    exception or `None`, exactly like `StationIndex.resolve()`.

CRS: all coordinates are WGS84 (EPSG:4326), as returned by Overpass and required
by the GeoJSON output. Reprojection to EPSG:3844 happens later in build-gpkg.
"""

from __future__ import annotations

import heapq
import math

from .domain import Coordinate
from .result import Maybe, Nothing, Some

# A graph node: (lon, lat) rounded to ~0.1 m. OSM emits identical coordinates for
# a shared node at a junction, so rounding to a fixed precision makes ways that
# meet there collapse onto the same key — that is what joins the network.
Node = tuple[float, float]
_PRECISION = 6
_EARTH_RADIUS_M = 6_371_000.0


def _node(lon: float, lat: float) -> Node:
    return (round(lon, _PRECISION), round(lat, _PRECISION))


def _coord(node: Node) -> Coordinate:
    return Coordinate(lon=node[0], lat=node[1])


def _haversine(a: Coordinate, b: Coordinate) -> float:
    """Great-circle distance between two WGS84 points, in metres."""
    p1, p2 = math.radians(a.lat), math.radians(b.lat)
    dphi = math.radians(b.lat - a.lat)
    dlmb = math.radians(b.lon - a.lon)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * _EARTH_RADIUS_M * math.asin(math.sqrt(h))


class RailNetwork:
    """Undirected weighted graph of rail tracks; routes between WGS84 points.

    Build it from an Overpass ``out geom`` response and route station pairs:

        net = RailNetwork.from_overpass(overpass_json)
        maybe_path = net.route(brasov, sighisoara)   # Maybe[list[Coordinate]]
        coords, routed = net.route_stops([c1, c2, c3])
    """

    def __init__(self, adjacency: dict[Node, list[tuple[Node, float]]]) -> None:
        self._adj = adjacency

    @classmethod
    def from_overpass(cls, overpass_data: dict) -> "RailNetwork":
        """Build the graph from a parsed Overpass JSON response (``out geom``).

        Each ``way`` element carries ``geometry`` as a list of ``{lat, lon}``;
        consecutive vertices become an undirected edge weighted by haversine
        length. Ways that share a junction coordinate are joined automatically
        (identical rounded node keys). Mirrors ``StationIndex.from_overpass``.
        """
        adjacency: dict[Node, list[tuple[Node, float]]] = {}

        def _edge(u: Node, v: Node) -> None:
            w = _haversine(_coord(u), _coord(v))
            adjacency.setdefault(u, []).append((v, w))
            adjacency.setdefault(v, []).append((u, w))

        for el in overpass_data.get("elements", []):
            if el.get("type") != "way":
                continue
            geometry = el.get("geometry")
            if not geometry:
                continue
            prev: Node | None = None
            for pt in geometry:
                cur = _node(pt["lon"], pt["lat"])
                if prev is not None and cur != prev:
                    _edge(prev, cur)
                prev = cur
        return cls(adjacency)

    def _snap(self, coord: Coordinate) -> Node | None:
        """Nearest graph node to ``coord`` (linear scan — fine for ~8 lines)."""
        best: Node | None = None
        best_d = math.inf
        for node in self._adj:
            d = _haversine(coord, _coord(node))
            if d < best_d:
                best_d, best = d, node
        return best

    def _dijkstra(self, src: Node, dst: Node) -> list[Node] | None:
        """Shortest path src→dst along the graph, or None if disconnected."""
        if src == dst:
            return [src]
        dist: dict[Node, float] = {src: 0.0}
        prev: dict[Node, Node] = {}
        heap: list[tuple[float, Node]] = [(0.0, src)]
        while heap:
            d, node = heapq.heappop(heap)
            if node == dst:
                break
            if d > dist.get(node, math.inf):
                continue  # stale heap entry
            for neighbor, w in self._adj.get(node, ()):
                nd = d + w
                if nd < dist.get(neighbor, math.inf):
                    dist[neighbor] = nd
                    prev[neighbor] = node
                    heapq.heappush(heap, (nd, neighbor))
        if dst not in dist:
            return None
        path = [dst]
        while path[-1] != src:
            path.append(prev[path[-1]])
        path.reverse()
        return path

    def route(self, a: Coordinate, b: Coordinate) -> Maybe[list[Coordinate]]:
        """Track-following path between two points, or ``Nothing`` if unreachable.

        Both points are snapped to the nearest rail node first. ``Nothing`` covers
        an empty network and a genuine gap between the two snapped nodes.
        """
        src, dst = self._snap(a), self._snap(b)
        if src is None or dst is None:
            return Nothing
        path = self._dijkstra(src, dst)
        if path is None:
            return Nothing
        return Some([_coord(n) for n in path])

    def route_stops(
        self, stops: list[Coordinate]
    ) -> tuple[list[Coordinate], bool]:
        """Route a full stop sequence, concatenating per-segment paths.

        Returns ``(coordinates, routed)``. ``routed`` is ``False`` if **any**
        segment fell back to a straight line between its two stops (a network gap)
        — the rest still follows the tracks. Shared segment endpoints are
        de-duplicated so the polyline has no repeated vertex at each stop.
        """
        if len(stops) < 2:
            return (list(stops), True)

        coords: list[Coordinate] = []
        routed = True
        for a, b in zip(stops, stops[1:]):
            segment = self.route(a, b)
            if segment.is_some:
                seg = segment.unwrap()
            else:
                seg = [a, b]          # gap → straight fallback for this leg
                routed = False
            if coords and seg and coords[-1] == seg[0]:
                seg = seg[1:]         # drop shared endpoint
            coords.extend(seg)
        return (coords, routed)
