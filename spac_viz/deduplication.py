"""Bounded geometric field-line deduplication."""
from __future__ import annotations
from collections import defaultdict
import numpy as np
from .classification import resample_polyline


def _key(p, tolerance):
    ends = sorted((tuple(np.round(p[0]/tolerance).astype(int)),
                   tuple(np.round(p[-1]/tolerance).astype(int))))
    length = np.linalg.norm(np.diff(p, axis=0), axis=1).sum()
    return (*ends, int(round(length/tolerance)))


def deduplicate(records, tolerance, comparison_points=32):
    if tolerance <= 0:
        raise ValueError("dedup_tolerance must be positive")
    buckets = defaultdict(list)
    kept = []
    removed = 0
    for record in records:
        p = np.asarray(record.coordinates)
        key = _key(p, tolerance)
        candidate_indices = []
        # Neighbor length bins avoid boundary misses while endpoint bins remain bounded.
        for dl in (-1, 0, 1):
            candidate_indices.extend(buckets.get((*key[:-1], key[-1]+dl), ()))
        q = resample_polyline(p, comparison_points)
        duplicate = False
        for idx in candidate_indices:
            r = resample_polyline(kept[idx].coordinates, comparison_points)
            if min(np.max(np.linalg.norm(q-r, axis=1)),
                   np.max(np.linalg.norm(q-r[::-1], axis=1))) <= tolerance:
                duplicate = True; break
        if duplicate:
            record.duplicate = True; removed += 1
        else:
            buckets[key].append(len(kept)); kept.append(record)
    return kept, removed
