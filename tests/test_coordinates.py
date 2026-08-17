import numpy as np
from spac_viz.seeds import spherical_to_cartesian,Seed

def test_latitude_colatitude():
    assert Seed("x",30,0,1).latitude_deg==60
    assert Seed("x",90,0,1).latitude_deg==0

def test_cardinal_points_right_handed():
    pts=spherical_to_cartesian(1,np.array([90,90,90,90,0,180]),
                               np.array([0,90,180,270,0,0]))
    expected=np.array([[1,0,0],[0,1,0],[-1,0,0],[0,-1,0],[0,0,1],[0,0,-1]])
    assert np.allclose(pts,expected,atol=1e-12)
    assert np.allclose(np.cross(pts[0],pts[1]),pts[4])
