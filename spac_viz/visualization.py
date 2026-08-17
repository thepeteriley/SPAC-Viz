"""Efficient PyVista map sphere and class-combined line geometry."""
from __future__ import annotations
from pathlib import Path
import numpy as np

COLORS = {"closed":"green", "open_positive":"red", "open_negative":"blue"}

def combined_lines(polylines):
    import pyvista as pv
    arrays = [np.asarray(x, float) for x in polylines if len(x) >= 2]
    if not arrays:
        return pv.PolyData()
    points = np.concatenate(arrays)
    cells, offset = [], 0
    for p in arrays:
        cells.extend([len(p), *range(offset, offset+len(p))]); offset += len(p)
    return pv.PolyData(points, lines=np.asarray(cells))

def map_sphere(smap, resolution=180):
    """Sphere with point Br sampled in native Carrington orientation."""
    import pyvista as pv
    from .adapt import sample_br_periodic
    # start_theta/end_theta avoid coincident duplicated poles; PyVista is right-handed.
    mesh = pv.Sphere(radius=1, theta_resolution=resolution, phi_resolution=max(30,resolution//2),
                     start_theta=0, end_theta=360, start_phi=0, end_phi=180)
    p = mesh.points
    lon = np.degrees(np.arctan2(p[:,1],p[:,0])) % 360
    lat = np.degrees(np.arcsin(np.clip(p[:,2],-1,1)))
    mesh["Br"] = np.array([sample_br_periodic(smap, lo, la) for lo,la in zip(lon,lat)])
    mesh["Carrington longitude"] = lon
    return mesh

def orientation_markers():
    import pyvista as pv
    labels = [(0,0,"0"),(90,0,"90"),(180,0,"180"),(270,0,"270"),(0,90,"N"),(0,-90,"S")]
    pts=[]; names=[]
    for lon,lat,name in labels:
        lr,br=np.deg2rad(lon),np.deg2rad(lat)
        pts.append([1.04*np.cos(br)*np.cos(lr),1.04*np.cos(br)*np.sin(lr),1.04*np.sin(br)])
        names.append(name)
    m=pv.PolyData(np.array(pts)); m["label"]=names
    return m

def build_plotter(smap, records, rss, clip=50, resolution=180, off_screen=False,
                  show_source_surface=False, title="", orientation_triad=True,
                  diagnostic_markers=False, show_photosphere=True):
    import pyvista as pv
    plotter=pv.Plotter(off_screen=off_screen); plotter.set_background("black")
    if show_photosphere:
        sphere=map_sphere(smap,resolution)
        plotter.add_mesh(sphere, scalars="Br", cmap="RdBu_r", clim=(-clip,clip),
                         scalar_bar_args={"title":"Br [G]"})
    for cls,color in COLORS.items():
        mesh=combined_lines([r.coordinates for r in records if r.classification==cls])
        if mesh.n_points: plotter.add_mesh(mesh,color=color,line_width=1,label={
            "closed":"closed","open_positive":"open, positive photospheric polarity",
            "open_negative":"open, negative photospheric polarity"}[cls])
    if show_source_surface and show_photosphere:
        plotter.add_mesh(pv.Sphere(radius=rss,theta_resolution=48,phi_resolution=24),
                         style="wireframe",color="white",opacity=.25)
    if diagnostic_markers:
        markers=orientation_markers()
        plotter.add_point_labels(markers,markers["label"],text_color="white",point_color="yellow")
    if orientation_triad: plotter.add_axes()
    plotter.add_legend(); plotter.add_title(title); plotter.view_isometric()
    return plotter

def save_scene(records, path):
    meshes=[]
    for cls in COLORS:
        m=combined_lines([r.coordinates for r in records if r.classification==cls])
        if m.n_points:
            m.cell_data["classification"]=np.full(m.n_cells,cls)
            meshes.append(m)
    if not meshes: raise ValueError("no resolved geometry to save")
    meshes[0].merge(meshes[1:]).save(Path(path))
