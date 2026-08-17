"""Chunk tracing and conversion from maintained sunkit-magex FieldLines."""
from __future__ import annotations
import logging
import numpy as np
from .classification import TraceRecord, clean_coordinates, classify_and_orient, resample_polyline, simplify_polyline
from .seeds import seeds_to_skycoord
from .model import trace_field_lines

LOG = logging.getLogger(__name__)

def fieldline_xyz(fieldline):
    """Convert FieldLine.coords Cartesian representation into R_sun floats."""
    import astropy.units as u
    c = fieldline.coords
    cart = c.cartesian
    return np.column_stack([cart.x.to_value(u.R_sun), cart.y.to_value(u.R_sun),
                            cart.z.to_value(u.R_sun)])

def process_chunk(output, tracer, seed_list, adapt_map, rss, endpoint_tolerance,
                  min_points, resample_points, simplify_tolerance, zero_threshold):
    from .adapt import sample_br_periodic
    sky = seeds_to_skycoord(seed_list, output.coordinate_frame)
    lines = trace_field_lines(output, tracer, sky)
    records = []
    for seed, line in zip(seed_list, lines, strict=True):
        xyz = clean_coordinates(fieldline_xyz(line), rss, min_points)
        if not len(xyz):
            rec = TraceRecord("unresolved", seed.boundary, seed.phi_deg, seed.latitude_deg,
                              seed.theta_deg, seed.radius, xyz, status="too_few_points")
        else:
            cls, xyz, br, photo, source = classify_and_orient(
                xyz, rss, endpoint_tolerance, lambda p: sample_br_periodic(adapt_map,p),
                zero_threshold)
            xyz = simplify_polyline(xyz, simplify_tolerance)
            xyz = resample_polyline(xyz, resample_points)
            rec = TraceRecord(cls, seed.boundary, seed.phi_deg, seed.latitude_deg,
                              seed.theta_deg, seed.radius, xyz,
                              status="ok" if cls != "unresolved" else "unresolved_endpoints",
                              photospheric_footpoint=photo, source_surface_endpoint=source,
                              br_gauss=br)
        records.append(rec)
    return records
