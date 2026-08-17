"""Explicit ADAPT ensemble FITS loading, validation, download and sampling."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import logging
import os
import re
import tempfile
import numpy as np

LOG = logging.getLogger(__name__)

@dataclass
class AdaptData:
    map: object
    source_path: Path
    observation_time: str
    realization: str
    ensemble_size: int


def _correct_documented_metadata(header):
    """Apply only conservative unit spelling fixes accepted by FITS/SunPy."""
    h = header.copy()
    if str(h.get("BUNIT", "")).strip().lower() in {"gauss", "g"}:
        h["BUNIT"] = "G"
    return h


def load_adapt(path, realization="0"):
    from astropy.io import fits
    import sunpy.map
    path = Path(path)
    with fits.open(path, memmap=False) as hdul:
        hdu = next((x for x in hdul if x.data is not None), None)
        if hdu is None:
            raise ValueError("FITS contains no image data")
        cube = np.asarray(hdu.data, dtype=float)
        header = _correct_documented_metadata(hdu.header)
    if cube.ndim == 2:
        cube = cube[None, ...]
    if cube.ndim != 3:
        raise ValueError(f"expected 2-D map or 3-D ADAPT ensemble, got shape {cube.shape}")
    if realization == "mean":
        plane = np.nanmean(cube, axis=0)
    else:
        try: idx = int(realization)
        except (TypeError, ValueError) as e: raise ValueError("realization must be an integer or 'mean'") from e
        if not 0 <= idx < cube.shape[0]:
            raise ValueError(f"realization {idx} outside [0, {cube.shape[0]-1}]")
        plane = cube[idx].copy()
    # Strip the ensemble axis, explicitly preserving two-dimensional WCS metadata.
    for key in ("NAXIS3", "CTYPE3", "CUNIT3", "CRPIX3", "CRVAL3", "CDELT3"):
        header.pop(key, None)
    header["NAXIS"] = 2; header["NAXIS1"] = plane.shape[1]; header["NAXIS2"] = plane.shape[0]
    smap = sunpy.map.Map(plane, header)
    validate_radial_carrington_map(smap)
    date = str(smap.date.utc.isot)
    return AdaptData(smap, path.resolve(), date, str(realization), cube.shape[0])


def validate_radial_carrington_map(smap):
    c1, c2 = (str(x).upper() for x in smap.coordinate_system)
    if not c1.startswith("CRLN") or not c2.startswith("CRLT"):
        raise ValueError(f"ADAPT map must be Carrington longitude/latitude; got {c1}, {c2}")
    content = " ".join(str(smap.meta.get(k, "")) for k in
                       ("CONTENT", "BTYPE", "BUNIT", "TELESCOP", "INSTRUME",
                        "MODEL", "MAPPARAM", "MAPDATA")).lower()
    if not any(x in content for x in ("gauss", "mag", "radial", "gong", "adapt")):
        raise ValueError("metadata does not identify a radial magnetic-field map")
    if smap.data.ndim != 2 or not np.any(np.isfinite(smap.data)):
        raise ValueError("map must be a finite 2-D magnetic field")


def sample_br_periodic(smap, point_or_lon, latitude_deg=None):
    """Bilinearly sample Br; longitude wraps and latitude only epsilon-clamps."""
    import astropy.units as u
    from astropy.coordinates import SkyCoord
    if latitude_deg is None:
        point = np.asarray(point_or_lon, float)
        r = np.linalg.norm(point)
        lon = np.degrees(np.arctan2(point[1], point[0])) % 360
        lat = np.degrees(np.arcsin(np.clip(point[2]/r, -1, 1)))
    else:
        lon, lat = float(point_or_lon) % 360, float(latitude_deg)
    if lat < -90-1e-8 or lat > 90+1e-8:
        raise ValueError("latitude outside physical range")
    lat = np.clip(lat, -90, 90)
    frame = smap.coordinate_frame
    coord = SkyCoord(lon=lon*u.deg, lat=lat*u.deg, radius=1*u.R_sun, frame=frame)
    xq, yq = smap.world_to_pixel(coord)
    x, y = float(xq.value), float(yq.value)
    ny, nx = smap.data.shape
    # WCS may report an equivalent longitude one image-width away.
    x %= nx
    y = np.clip(y, 0, ny-1)
    x0, y0 = int(np.floor(x)) % nx, int(np.floor(y))
    x1, y1 = (x0+1) % nx, min(y0+1, ny-1)
    fx, fy = x-np.floor(x), y-y0
    d = np.asarray(smap.data)
    return float((1-fy)*((1-fx)*d[y0,x0]+fx*d[y0,x1]) +
                 fy*((1-fx)*d[y1,x0]+fx*d[y1,x1]))


def download_adapt(output_dir, *, latest=False, time=None, recent_days=14, overwrite=False):
    from astropy.time import Time
    import astropy.units as u
    from sunpy.net import Fido, attrs as a
    now = Time.now()
    if latest:
        start, end = now - recent_days*u.day, now
    elif time:
        target = Time(time); start, end = target-3*u.hour, target+3*u.hour
    else:
        raise ValueError("download requires latest or time")
    query = Fido.search(a.Time(start, end), a.Instrument("ADAPT"), a.adapt.ADAPTLonType("0"))
    rows = []
    for response in query:
        for i, row in enumerate(response):
            rows.append((Time(row["Start Time"]), response, i))
    if not rows:
        LOG.warning("SunPy Fido returned no ADAPT results; trying the official NSO "
                    "directory-listing fallback for %s .. %s", start.isot, end.isot)
        return _download_from_nso_listing(output_dir, start, end, target=Time(time) if time else None,
                                          overwrite=overwrite)
    if time:
        target = Time(time)
        chosen = min(rows, key=lambda x: abs((x[0]-target).sec))
    else:
        chosen = max(rows, key=lambda x: x[0])
    selected_time, response, index = chosen
    age = (now-selected_time).to_value(u.day)
    if latest and age > recent_days:
        raise RuntimeError(f"newest ADAPT result is unexpectedly old ({age:.1f} days)")
    LOG.info("Selected ADAPT result timestamp=%s record=%s", selected_time.utc.isot, response[index])
    fetched = Fido.fetch(response[index:index+1], path=Path(output_dir), overwrite=overwrite)
    if not fetched:
        raise RuntimeError("ADAPT download failed")
    LOG.info("Downloaded ADAPT file %s at timestamp %s", fetched[0], selected_time.utc.isot)
    return Path(fetched[0])


_NSO_FILE_RE = re.compile(
    r'href="(?P<name>adapt(?P<filetype>\d)(?P<lontype>\d)\d{3}_'
    r'[^"]*?_(?P<timestamp>\d{12})_[^"]+?\.fts\.gz)"'
)


def _listing_candidates(html, start, end):
    """Parse official NSO listing links, retaining longitude type 0 only."""
    from astropy.time import Time
    found = {}
    for match in _NSO_FILE_RE.finditer(html):
        if match.group("lontype") != "0":
            continue
        timestamp = Time.strptime(match.group("timestamp"), "%Y%m%d%H%M")
        if start <= timestamp <= end:
            found[match.group("name")] = timestamp
    return [(timestamp, name) for name, timestamp in found.items()]


def _download_from_nso_listing(output_dir, start, end, target=None, overwrite=False):
    """Fallback for known Fido scraper gaps; accesses only official NSO HTTPS."""
    from urllib.request import urlopen
    import ssl
    import certifi
    tls = ssl.create_default_context(cafile=certifi.where())
    years = range(start.datetime.year, end.datetime.year + 1)
    candidates = []
    base = "https://gong.nso.edu/adapt/maps/gong"
    for year in years:
        url = f"{base}/{year}/"
        try:
            with urlopen(url, timeout=60, context=tls) as response:
                html = response.read().decode("utf-8", "replace")
        except Exception as exc:
            LOG.warning("Could not read NSO listing %s: %s", url, exc)
            continue
        candidates.extend((timestamp, name, url) for timestamp, name
                          in _listing_candidates(html, start, end))
    if not candidates:
        raise RuntimeError(f"no longitude-type-0 ADAPT maps found in {start.isot} .. {end.isot}")
    if target is None:
        selected_time, filename, listing_url = max(candidates, key=lambda x: x[0])
    else:
        selected_time, filename, listing_url = min(
            candidates, key=lambda x: abs((x[0] - target).sec))
    source_url = listing_url + filename
    output_dir = Path(output_dir); output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / filename
    if destination.exists() and not overwrite:
        LOG.info("Selected ADAPT file=%s timestamp=%s (existing local file)",
                 filename, selected_time.utc.isot)
        return destination
    LOG.info("Selected ADAPT file=%s timestamp=%s url=%s",
             filename, selected_time.utc.isot, source_url)
    fd, tmp = tempfile.mkstemp(prefix=filename + ".", suffix=".tmp", dir=output_dir)
    try:
        with os.fdopen(fd, "wb") as out, urlopen(source_url, timeout=120, context=tls) as response:
            while block := response.read(1024 * 1024):
                out.write(block)
            out.flush(); os.fsync(out.fileno())
        os.replace(tmp, destination)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    LOG.info("Downloaded ADAPT file %s at timestamp %s", destination, selected_time.utc.isot)
    return destination
