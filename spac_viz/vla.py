"""Atomic Digistar P/L ASCII writer and strict validator."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import os, tempfile
import numpy as np

FILENAMES = {
    "open_negative": "pfss_blue_open_negative.vla",
    "closed": "pfss_green_closed.vla",
    "open_positive": "pfss_red_open_positive.vla",
}

# Digistar directives requested by the target D4 workflow.  The exported
# coordinate records are correspondingly written as input X, Z, Y, which is a
# handedness-changing axis permutation into this LEFT coordinate system.
VLA_HEADER = (
    "set parametric NON_PARAMETRIC",
    "set filecontent LINES",
    "set filetype New",
    "set depthcue 0",
    "set defaultdraw STELLAR",
    "set coordsys LEFT",
)

@dataclass(frozen=True)
class VLAStats:
    polylines: int
    vertices: int


def write_vla(path, polylines, metadata, scale=1.0, minimal=False, overwrite=False):
    path = Path(path)
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    arrays = [np.asarray(p, float) for p in polylines]
    if any(len(p) < 2 or not np.all(np.isfinite(p)) for p in arrays):
        raise ValueError("VLA polylines require at least two finite vertices")
    stats = VLAStats(len(arrays), sum(map(len, arrays)))
    fd, tmp = tempfile.mkstemp(prefix=path.name+".", suffix=".tmp", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", newline="\n", encoding="ascii") as f:
            if not minimal:
                for directive in VLA_HEADER:
                    f.write(directive + "\n")
                for key, value in metadata.items():
                    f.write(f"; {key}: {value}\n")
                f.write(f"; polylines: {stats.polylines}\n; vertices: {stats.vertices}\n")
            for p in arrays:
                for i, xyz in enumerate(p * scale):
                    output_xyz = xyz[[0, 2, 1]]
                    f.write(("P" if i == 0 else "L") + " " +
                            " ".join(f"{v:.10g}" for v in output_xyz) + "\n")
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return stats


def validate_vla(path, expected_class=None):
    polylines, current, meta, directives = [], None, {}, []
    for number, raw in enumerate(Path(path).read_text(encoding="ascii").splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if line.startswith(";"):
            body = line[1:].strip()
            if ":" in body:
                k, v = body.split(":", 1); meta[k.strip()] = v.strip()
            continue
        if line.lower().startswith("set "):
            if current is not None:
                raise ValueError(f"line {number}: header directive after geometry")
            if line not in VLA_HEADER:
                raise ValueError(f"line {number}: unsupported header directive")
            if line in directives:
                raise ValueError(f"line {number}: duplicate header directive")
            directives.append(line)
            continue
        fields = line.split()
        if len(fields) != 4 or fields[0] not in {"P", "L"}:
            raise ValueError(f"line {number}: invalid record")
        try:
            xyz = np.array([float(x) for x in fields[1:]])
        except ValueError as e:
            raise ValueError(f"line {number}: invalid coordinate") from e
        if not np.all(np.isfinite(xyz)):
            raise ValueError(f"line {number}: non-finite coordinate")
        if fields[0] == "P":
            if current is not None:
                if len(current) < 2: raise ValueError("polyline lacks L")
                polylines.append(np.array(current))
            current = [xyz]
        elif current is None:
            raise ValueError(f"line {number}: L before P")
        else:
            current.append(xyz)
    if current is not None:
        if len(current) < 2: raise ValueError("polyline lacks L")
        polylines.append(np.array(current))
    vertices = sum(map(len, polylines))
    if "polylines" in meta and int(meta["polylines"]) != len(polylines):
        raise ValueError("polyline metadata mismatch")
    if "vertices" in meta and int(meta["vertices"]) != vertices:
        raise ValueError("vertex metadata mismatch")
    if expected_class and meta.get("classification") not in (None, expected_class):
        raise ValueError("classification mismatch")
    if directives and tuple(directives) != VLA_HEADER:
        raise ValueError("incomplete or incorrectly ordered VLA header")
    return polylines, meta, VLAStats(len(polylines), vertices)
