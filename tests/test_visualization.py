import numpy as np
import pyvista as pv
from spac_viz.visualization import combined_lines,map_sphere,orientation_markers
from spac_viz.adapt import load_adapt

def test_combined_mesh_and_markers(synthetic_adapt):
    m=combined_lines([np.array([[1,0,0],[2,0,0]]),np.array([[0,1,0],[0,2,0]])])
    assert m.n_cells==2 and m.n_points==4
    marks=orientation_markers()
    assert set(marks["label"])=={"0","90","180","270","N","S"}
    smap=load_adapt(synthetic_adapt,"0").map
    sphere=map_sphere(smap,30)
    assert sphere.n_points>0 and np.all(np.isfinite(sphere["Br"]))

def test_offscreen_plotter_construction(synthetic_adapt):
    smap=load_adapt(synthetic_adapt,"0").map
    pl=pv.Plotter(off_screen=True,window_size=(128,128))
    pl.add_mesh(map_sphere(smap,30),scalars="Br")
    assert pl.off_screen and len(pl.actors)>=1
    pl.close()
