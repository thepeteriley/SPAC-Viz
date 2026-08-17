import os
from pathlib import Path
os.environ.setdefault("SUNPY_CONFIGDIR", str(Path(".sunpy-config").resolve()))
os.environ.setdefault("SUNPY_DOWNLOADDIR", str(Path(".sunpy-data").resolve()))
os.environ.setdefault("MPLCONFIGDIR", str(Path(".mpl-config").resolve()))
os.environ.setdefault("XDG_CACHE_HOME", str(Path(".cache").resolve()))

import numpy as np
import pytest

@pytest.fixture
def synthetic_adapt(tmp_path):
    from astropy.io import fits
    from astropy.time import Time
    from sunpy.coordinates import get_earth
    from sunpy.map.header_helper import make_heliographic_header
    shape=(24,48)
    h=make_heliographic_header(Time("2026-07-30T12:00:00"),get_earth("2026-07-30T12:00:00"),
                              shape,frame="carrington",projection_code="CEA")
    h["BUNIT"]="G"; h["CONTENT"]="ADAPT radial magnetic field"; h["INSTRUME"]="ADAPT"
    lat=np.linspace(-1,1,shape[0])
    dipole=np.repeat(lat[:,None],shape[1],axis=1)*10
    cube=np.stack((dipole,-dipole))
    path=tmp_path/"synthetic_adapt.fits"
    fits.writeto(path,cube,fits.Header(dict(h)),overwrite=True)
    return path
