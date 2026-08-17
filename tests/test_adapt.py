import numpy as np
import pytest
from spac_viz.adapt import load_adapt,sample_br_periodic

def test_explicit_realization_and_mean(synthetic_adapt):
    a=load_adapt(synthetic_adapt,"0"); b=load_adapt(synthetic_adapt,"mean")
    assert a.ensemble_size==2 and a.map.data.ndim==2
    assert np.max(np.abs(b.map.data)) < 1e-12
    with pytest.raises(ValueError): load_adapt(synthetic_adapt,"12")

def test_periodic_seam_sampling(synthetic_adapt):
    a=load_adapt(synthetic_adapt,"0")
    for lat, sign in [(60,1),(-60,-1)]:
        left=sample_br_periodic(a.map,359.99,lat)
        right=sample_br_periodic(a.map,.01,lat)
        assert np.sign(left)==sign and np.sign(right)==sign
        assert abs(left-right)<1e-2

def test_orientation_native_wcs(synthetic_adapt):
    import astropy.units as u
    a=load_adapt(synthetic_adapt,"0")
    # Pixel x increases in Carrington longitude, y increases northward.
    c00=a.map.pixel_to_world(0*u.pix,0*u.pix); c10=a.map.pixel_to_world(1*u.pix,0*u.pix)
    c01=a.map.pixel_to_world(0*u.pix,1*u.pix)
    dlon=((c10.lon.deg-c00.lon.deg+180)%360)-180
    assert dlon > 0
    assert c01.lat.deg > c00.lat.deg

def test_official_listing_parser_filters_lon_type():
    from astropy.time import Time
    from spac_viz.adapt import _listing_candidates
    html='''<a href="adapt40311_044012_202607301400_i00010600n1.fts.gz">a</a>
            <a href="adapt41311_044012_202607301600_i00005600n1.fts.gz">b</a>
            <a href="adapt40311_044012_202607301600_i00005600n1.fts.gz">c</a>'''
    rows=_listing_candidates(html,Time("2026-07-30"),Time("2026-07-31"))
    assert [x[1] for x in rows]==[
        "adapt40311_044012_202607301400_i00010600n1.fts.gz",
        "adapt40311_044012_202607301600_i00005600n1.fts.gz"]
