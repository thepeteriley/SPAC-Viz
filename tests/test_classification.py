import numpy as np
from spac_viz.classification import classify_and_orient,clean_coordinates,resample_polyline,simplify_polyline

def line(r0,r1): return np.column_stack((np.linspace(r0,r1,5),np.zeros(5),np.zeros(5)))

def test_all_classes_and_open_orientation():
    c,p,br,photo,source=classify_and_orient(line(2.5,1),2.5,.02,lambda p:3)
    assert c=="open_positive" and np.isclose(np.linalg.norm(p[0]),1) and br==3
    assert classify_and_orient(line(1,2.5),2.5,.02,lambda p:-2)[0]=="open_negative"
    closed=np.array([[1,0,0],[1.2,0,0],[-1,0,0]])
    assert classify_and_orient(closed,2.5,.02,lambda p:1)[0]=="closed"
    assert classify_and_orient(line(1.2,2),2.5,.02,lambda p:1)[0]=="unresolved"
    assert classify_and_orient(line(1,2.5),2.5,.02,lambda p:0)[0]=="unresolved"

def test_clean_resample_simplify():
    p=np.array([[1,0,0],[1,0,0],[np.nan,0,0],[1.5,0,0],[2,0,0]])
    q=clean_coordinates(p,2.5,2)
    assert np.all(np.isfinite(q)) and len(q)==3
    assert len(resample_polyline(q,7))==7
    assert len(simplify_polyline(q,.01))==2
