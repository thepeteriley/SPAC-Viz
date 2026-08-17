"""Trace cleaning, endpoint classification, orientation and resampling."""
from __future__ import annotations
from dataclasses import dataclass, asdict
import numpy as np


@dataclass
class TraceRecord:
    classification: str
    seed_boundary: str
    seed_phi_deg: float
    seed_latitude_deg: float
    seed_theta_deg: float
    seed_radius: float
    coordinates: np.ndarray
    status: str = "ok"
    photospheric_footpoint: list[float] | None = None
    source_surface_endpoint: list[float] | None = None
    br_gauss: float | None = None
    duplicate: bool = False

    def metadata(self):
        d = asdict(self)
        d.pop("coordinates")
        return d


def clean_coordinates(xyz, rss, min_points=2):
    a = np.asarray(xyz, dtype=float).reshape(-1, 3)
    a = a[np.all(np.isfinite(a), axis=1)]
    if len(a):
        a = a[np.r_[True, np.linalg.norm(np.diff(a, axis=0), axis=1) > 1e-12]]
        r = np.linalg.norm(a, axis=1)
        a = a[(r >= 1 - 0.1) & (r <= rss + 0.1)]
    return a if len(a) >= min_points else np.empty((0, 3))


def endpoint_kind(point, rss, tolerance):
    r = float(np.linalg.norm(point))
    if abs(r - 1.0) <= tolerance:
        return "photosphere"
    if abs(r - rss) <= tolerance:
        return "source_surface"
    return "unresolved"


def classify_and_orient(xyz, rss, tolerance, sample_br, zero_threshold=1e-9):
    """Return class, deterministically oriented coordinates, Br, endpoint data."""
    a = np.asarray(xyz, float)
    k0, k1 = endpoint_kind(a[0], rss, tolerance), endpoint_kind(a[-1], rss, tolerance)
    br = None
    photo = source = None
    if k0 == k1 == "photosphere":
        # Direction-independent deterministic lexicographic ordering.
        if tuple(np.round(a[-1], 12)) < tuple(np.round(a[0], 12)):
            a = a[::-1].copy()
        return "closed", a, br, a[0].tolist(), None
    if {k0, k1} == {"photosphere", "source_surface"}:
        if k1 == "photosphere":
            a = a[::-1].copy()
        photo, source = a[0].tolist(), a[-1].tolist()
        br = float(sample_br(a[0]))
        if not np.isfinite(br) or abs(br) <= zero_threshold:
            return "unresolved", a, br, photo, source
        return ("open_positive" if br > 0 else "open_negative"), a, br, photo, source
    return "unresolved", a, br, photo, source


def resample_polyline(points, count):
    p = np.asarray(points, float)
    if not count or count == len(p):
        return p.copy()
    if count < 2:
        raise ValueError("resample_points must be zero or >= 2")
    d = np.r_[0.0, np.cumsum(np.linalg.norm(np.diff(p, axis=0), axis=1))]
    if d[-1] == 0:
        return p[[0, -1]]
    q = np.linspace(0, d[-1], count)
    return np.column_stack([np.interp(q, d, p[:, i]) for i in range(3)])


def simplify_polyline(points, tolerance):
    p = np.asarray(points, float)
    if tolerance <= 0 or len(p) <= 2:
        return p.copy()
    keep = np.zeros(len(p), bool); keep[[0, -1]] = True
    stack = [(0, len(p)-1)]
    while stack:
        i, j = stack.pop()
        v = p[j] - p[i]
        if np.dot(v, v) == 0:
            dist = np.linalg.norm(p[i+1:j] - p[i], axis=1)
        else:
            w = p[i+1:j] - p[i]
            t = np.clip(w @ v / (v @ v), 0, 1)
            dist = np.linalg.norm(w - t[:, None]*v, axis=1)
        if len(dist) and dist.max() > tolerance:
            k = i + 1 + int(dist.argmax()); keep[k] = True
            stack.extend(((i, k), (k, j)))
    return p[keep]
