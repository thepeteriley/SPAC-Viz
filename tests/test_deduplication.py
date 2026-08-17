import numpy as np
from spac_viz.classification import TraceRecord
from spac_viz.deduplication import deduplicate

def rec(p): return TraceRecord("closed","surface",0,0,90,1.001,np.asarray(p,float))
def test_reversal_and_determinism():
    p=np.array([[1,0,0],[1.2,.2,0],[1,0.4,0]])
    kept,n=deduplicate([rec(p),rec(p[::-1]),rec(p+1)],.001)
    assert n==1 and len(kept)==2
    assert np.array_equal(kept[0].coordinates,p)
