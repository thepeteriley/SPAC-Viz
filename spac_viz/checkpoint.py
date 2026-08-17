"""Atomic, resumable per-chunk NPZ+JSON trace storage."""
from __future__ import annotations
from pathlib import Path
import hashlib, json, os, tempfile
import numpy as np
from .classification import TraceRecord

def config_digest(metadata):
    return hashlib.sha256(json.dumps(metadata, sort_keys=True, default=str).encode()).hexdigest()

class CheckpointStore:
    def __init__(self, directory, metadata, resume=False, overwrite=False):
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
        self.overwrite = overwrite
        self.metadata = dict(metadata); self.metadata["digest"] = config_digest(metadata)
        manifest = self.directory/"manifest.json"
        if manifest.exists():
            old = json.loads(manifest.read_text())
            if old.get("digest") != self.metadata["digest"]:
                raise ValueError("checkpoint configuration is incompatible")
            if not resume and not overwrite:
                raise FileExistsError(f"checkpoint exists: {manifest}")
        else:
            _atomic_text(manifest, json.dumps(self.metadata, indent=2, sort_keys=True))

    def chunk_path(self, boundary, index):
        return self.directory/f"{boundary}_{index:06d}.npz"

    def completed(self, boundary, index):
        return self.chunk_path(boundary,index).exists() and not self.overwrite

    def write_chunk(self, boundary, index, records):
        path = self.chunk_path(boundary,index)
        flat, offsets, metas = [], [0], []
        for r in records:
            flat.append(r.coordinates); offsets.append(offsets[-1]+len(r.coordinates)); metas.append(r.metadata())
        coords = np.concatenate(flat) if flat else np.empty((0,3))
        fd, tmp = tempfile.mkstemp(prefix=path.name+".", suffix=".tmp", dir=path.parent)
        os.close(fd)
        try:
            with open(tmp, "wb") as f:
                np.savez_compressed(f, coordinates=coords, offsets=np.array(offsets),
                                    records=np.array(json.dumps(metas)))
                f.flush(); os.fsync(f.fileno())
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)

    def read_all(self):
        for path in sorted(self.directory.glob("*.npz")):
            with np.load(path, allow_pickle=False) as z:
                coords, offsets = z["coordinates"], z["offsets"]
                metas = json.loads(str(z["records"]))
            for i, m in enumerate(metas):
                yield TraceRecord(coordinates=coords[offsets[i]:offsets[i+1]].copy(), **m)

def _atomic_text(path, text):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(prefix=path.name+".", suffix=".tmp", dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text); f.flush(); os.fsync(f.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
