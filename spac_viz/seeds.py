"""Seed grids and coordinate conventions."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Seed:
    boundary: str
    theta_deg: float
    phi_deg: float
    radius: float

    @property
    def latitude_deg(self) -> float:
        return 90.0 - self.theta_deg


def angular_values(start: float, stop: float, spacing: float, *, longitude=False) -> np.ndarray:
    if spacing <= 0 or stop < start:
        raise ValueError("spacing must be positive and stop >= start")
    values = np.arange(start, stop + max(1e-10, spacing * 1e-9), spacing, dtype=float)
    values = values[values <= stop + 1e-9]
    if longitude:
        values = np.mod(values, 360.0)
        # stable unique prevents 0/360 duplication
        _, indices = np.unique(np.round(values, 10), return_index=True)
        values = values[np.sort(indices)]
    return values


def seed_count(theta_min, theta_max, phi_min, phi_max, spacing) -> int:
    return len(angular_values(theta_min, theta_max, spacing)) * len(
        angular_values(phi_min, phi_max, spacing, longitude=True)
    )


def iter_seed_chunks(boundary, theta_min, theta_max, phi_min, phi_max, spacing, radius, chunk_size):
    """Yield deterministic theta-major (``meshgrid(indexing='ij')``) chunks."""
    if not (0 < theta_min <= theta_max < 180):
        raise ValueError("seeds must not include either pole")
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    theta = angular_values(theta_min, theta_max, spacing)
    phi = angular_values(phi_min, phi_max, spacing, longitude=True)
    chunk: list[Seed] = []
    for t in theta:
        for p in phi:
            chunk.append(Seed(boundary, float(t), float(p), float(radius)))
            if len(chunk) == chunk_size:
                yield chunk
                chunk = []
    if chunk:
        yield chunk


def spherical_to_cartesian(radius, theta_deg, phi_deg):
    """Right-handed HGC: x at phi=0, y at phi=90, z north."""
    t, p = np.deg2rad(theta_deg), np.deg2rad(phi_deg)
    return np.stack((radius*np.sin(t)*np.cos(p), radius*np.sin(t)*np.sin(p),
                     radius*np.cos(t)), axis=-1)


def seeds_to_skycoord(seeds, frame):
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    lon = np.array([s.phi_deg for s in seeds]) * u.deg
    lat = np.array([s.latitude_deg for s in seeds]) * u.deg
    radius = np.array([s.radius for s in seeds]) * u.R_sun
    return SkyCoord(lon=lon, lat=lat, radius=radius, frame=frame)
