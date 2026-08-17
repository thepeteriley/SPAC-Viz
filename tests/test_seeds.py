import numpy as np
from spac_viz.seeds import seed_count,iter_seed_chunks,angular_values
from spac_viz.cli import parser

def test_counts():
    assert seed_count(.5,179.5,0,359,1)==180*360
    assert seed_count(15,165,0,330,30)==6*12
    assert seed_count(30,150,0,270,90)==2*4

def test_no_seam_duplicate_or_poles():
    phi=angular_values(0,360,30,longitude=True)
    assert len(phi)==12 and len(np.unique(phi))==12 and 360 not in phi
    seeds=sum(iter_seed_chunks("surface",.5,179.5,0,359,1,1.001,10000),[])
    assert all(s.theta_deg not in (0,180) for s in seeds)

def test_order_theta_major():
    s=sum(iter_seed_chunks("x",30,60,0,90,30,1.1,99),[])
    assert [(x.theta_deg,x.phi_deg) for x in s]==[(30,0),(30,30),(30,60),(30,90),
                                                   (60,0),(60,30),(60,60),(60,90)]

def test_cli_defaults_trace_photosphere_at_two_degrees():
    args=parser().parse_args(["--adapt-file","map.fits"])
    assert args.surface_spacing_deg==2.0
    assert args.outer_spacing_deg==2.0
    assert args.outer_seeds is False

def test_outer_seeds_are_explicit_opt_in():
    args=parser().parse_args(["--adapt-file","map.fits","--outer-seeds"])
    assert args.outer_seeds is True
