"""Command line orchestration."""
from __future__ import annotations
import argparse, json, logging, os, sys
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter

LOG = logging.getLogger("spac_viz")

def parser():
    p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    src=p.add_mutually_exclusive_group(required=True)
    src.add_argument("--adapt-file",type=Path)
    src.add_argument("--download-latest",action="store_true")
    src.add_argument("--download-time")
    p.add_argument("--download-recent-days",type=float,default=14)
    p.add_argument("--realization",default="0")
    p.add_argument("--output-dir",type=Path,default=Path("pfss_output"))
    p.add_argument("--rss",type=float,default=2.5); p.add_argument("--nrho",type=int,default=60)
    p.add_argument("--surface-spacing-deg",type=float,default=2.0)
    p.add_argument("--outer-spacing-deg",type=float,default=2.0)
    p.add_argument("--outer-seeds",action=argparse.BooleanOptionalAction,default=False,
                   help="also seed at the source surface; disabled by default because every seed is traced bidirectionally")
    p.add_argument("--surface-seed-radius",type=float,default=1.001)
    p.add_argument("--outer-seed-radius",type=float)
    p.add_argument("--theta-min-deg",type=float,default=.5); p.add_argument("--theta-max-deg",type=float,default=179.5)
    p.add_argument("--phi-min-deg",type=float,default=0.0); p.add_argument("--phi-max-deg",type=float,default=359.0)
    p.add_argument("--trace-chunk-size",type=int,default=1000)
    p.add_argument("--tracer",choices=("performance","python"),default="performance")
    p.add_argument("--tracer-step-size",type=float,default=.5)
    p.add_argument("--max-steps",default="auto",help="integer or auto")
    p.add_argument("--endpoint-tolerance",type=float,default=.02,help="solar radii")
    p.add_argument("--dedup-tolerance",type=float,default=.01,help="solar radii")
    p.add_argument("--min-points",type=int,default=2)
    p.add_argument("--resample-points",type=int,default=0)
    p.add_argument("--simplify-tolerance",type=float,default=0)
    p.add_argument("--zero-threshold",type=float,default=1e-9,help="gauss")
    p.add_argument("--map-clip-gauss",type=float,default=50)
    p.add_argument("--sphere-resolution",type=int,default=180)
    p.add_argument("--plot",action="store_true"); p.add_argument("--off-screen",action="store_true")
    p.add_argument("--save-screenshot",type=Path); p.add_argument("--save-pyvista",type=Path)
    p.add_argument("--show-source-surface",action="store_true")
    p.add_argument("--field-lines-only",action="store_true",
                   help="draw field lines only; omit all photospheric and source-surface geometry")
    p.add_argument("--orientation-diagnostic",action="store_true")
    p.add_argument("--no-orientation-triad",action="store_true")
    p.add_argument("--export-vla",action="store_true"); p.add_argument("--export-combined-vla",action="store_true")
    p.add_argument("--vla-scale",type=float,default=1); p.add_argument("--vla-minimal",action="store_true")
    p.add_argument("--no-deduplicate",action="store_true")
    p.add_argument("--resume",action="store_true"); p.add_argument("--overwrite",action="store_true")
    p.add_argument("--log-level",choices=("DEBUG","INFO","WARNING","ERROR"),default="INFO")
    return p

def _validate(a):
    if a.outer_seed_radius is None: a.outer_seed_radius=a.rss-.001
    if not (1 < a.surface_seed_radius < a.rss): raise ValueError("surface seed radius must be inside PFSS domain")
    if not (1 < a.outer_seed_radius < a.rss): raise ValueError("outer seed radius must be inside PFSS domain")
    if a.rss <= 1 or a.nrho < 2: raise ValueError("rss > 1 and nrho >= 2 required")
    if a.max_steps != "auto":
        a.max_steps=int(a.max_steps)
        if a.max_steps < 1: raise ValueError("max_steps must be positive")
    if a.resample_points == 1: raise ValueError("resample_points must be zero or >=2")
    if a.min_points < 2: raise ValueError("min_points must be >=2")

def run(args):
    from .adapt import load_adapt, download_adapt
    from .model import calculate_pfss, make_tracer
    from .seeds import seed_count, iter_seed_chunks
    from .checkpoint import CheckpointStore
    from .tracing import process_chunk
    from .deduplication import deduplicate
    from .vla import write_vla, validate_vla, FILENAMES
    a=args; _validate(a)
    a.output_dir.mkdir(parents=True,exist_ok=True)
    if a.download_latest or a.download_time:
        adapt_path=download_adapt(a.output_dir/"downloads",latest=a.download_latest,time=a.download_time,
                                  recent_days=a.download_recent_days,overwrite=a.overwrite)
    else: adapt_path=a.adapt_file
    adapt=load_adapt(adapt_path,a.realization)
    ns=seed_count(a.theta_min_deg,a.theta_max_deg,a.phi_min_deg,a.phi_max_deg,a.surface_spacing_deg)
    no=(seed_count(a.theta_min_deg,a.theta_max_deg,a.phi_min_deg,a.phi_max_deg,
                   a.outer_spacing_deg) if a.outer_seeds else 0)
    LOG.info("Estimated seeds: surface=%d source-surface=%d total=%d",ns,no,ns+no)
    if a.surface_spacing_deg <= 1 or a.outer_spacing_deg <= 1:
        LOG.warning("FULL 1-degree run requested: %d seeds; expect substantial CPU, RAM, and disk time",ns+no)
    model_meta={"adapt_file":str(Path(adapt_path).resolve()),"adapt_timestamp":adapt.observation_time,
                "realization":adapt.realization,"rss":a.rss,"nrho":a.nrho,
                "theta_range":[a.theta_min_deg,a.theta_max_deg],"phi_range":[a.phi_min_deg,a.phi_max_deg],
                "surface_spacing":a.surface_spacing_deg,"outer_spacing":a.outer_spacing_deg,
                "outer_seeds":a.outer_seeds,
                "surface_radius":a.surface_seed_radius,"outer_radius":a.outer_seed_radius,
                "tracer":a.tracer,"step_size":a.tracer_step_size,"max_steps":a.max_steps,
                "endpoint_tolerance":a.endpoint_tolerance,"min_points":a.min_points,
                "resample_points":a.resample_points,"simplify_tolerance":a.simplify_tolerance,
                "zero_threshold":a.zero_threshold}
    store=CheckpointStore(a.output_dir/"checkpoints",model_meta,resume=a.resume,overwrite=a.overwrite)
    LOG.info("Calculating PFSS nrho=%d rss=%.4g",a.nrho,a.rss)
    output=calculate_pfss(adapt.map,a.nrho,a.rss)
    tracer=make_tracer(a.tracer,a.tracer_step_size,a.max_steps)
    boundaries=[("surface",a.surface_spacing_deg,a.surface_seed_radius,ns)]
    if a.outer_seeds:
        boundaries.append(("source_surface",a.outer_spacing_deg,a.outer_seed_radius,no))
    try:
        for boundary,spacing,radius,total in boundaries:
            chunks=iter_seed_chunks(boundary,a.theta_min_deg,a.theta_max_deg,a.phi_min_deg,
                                    a.phi_max_deg,spacing,radius,a.trace_chunk_size)
            nchunks=(total+a.trace_chunk_size-1)//a.trace_chunk_size
            for idx,seeds in enumerate(chunks):
                if store.completed(boundary,idx):
                    LOG.info("%s chunk %d/%d already complete",boundary,idx+1,nchunks); continue
                records=process_chunk(output,tracer,seeds,adapt.map,a.rss,a.endpoint_tolerance,
                                      a.min_points,a.resample_points,a.simplify_tolerance,a.zero_threshold)
                store.write_chunk(boundary,idx,records)
                LOG.info("%s chunk %d/%d complete (%d seeds)",boundary,idx+1,nchunks,len(seeds))
    except KeyboardInterrupt:
        LOG.warning("Interrupted after last atomic chunk; resume from %s",store.directory)
        return 130
    all_records=list(store.read_all())
    resolved=[r for r in all_records if r.classification!="unresolved"]
    duplicate_count=0
    if not a.no_deduplicate:
        unique=[]
        for cls in ("closed","open_positive","open_negative"):
            part,removed=deduplicate([r for r in resolved if r.classification==cls],a.dedup_tolerance)
            unique.extend(part); duplicate_count+=removed
    else: unique=resolved
    # A compatible resume reconstructs the consolidated file from atomic
    # checkpoints; replacing that derived file is safe and avoids retracing.
    _save_results(a.output_dir/"trace_results.npz",unique,model_meta,a.overwrite or a.resume)
    counts=Counter(r.classification for r in unique)
    vstats={}
    if a.export_vla:
        meta={"generated_utc":datetime.now(timezone.utc).isoformat(),"adapt_observation":adapt.observation_time,
              "adapt_source":Path(adapt_path).name,"realization":adapt.realization,"rss":a.rss,"nrho":a.nrho,
              "surface_spacing_deg":a.surface_spacing_deg,"outer_spacing_deg":a.outer_spacing_deg,
              "coordinate_units":f"{a.vla_scale:g} scaled solar radii"}
        for cls,filename in FILENAMES.items():
            cm={**meta,"label":filename.removesuffix(".vla"),"classification":cls}
            path=a.output_dir/filename
            vstats[cls]=write_vla(path,[r.coordinates for r in unique if r.classification==cls],
                                  cm,a.vla_scale,a.vla_minimal,a.overwrite or a.resume)
            validate_vla(path,cls)
        if a.export_combined_vla:
            cm={**meta,"label":"combined diagnostic","classification":"combined"}
            write_vla(a.output_dir/"pfss_combined_diagnostic.vla",[r.coordinates for r in unique],
                      cm,a.vla_scale,a.vla_minimal,a.overwrite or a.resume)
    if a.plot or a.save_screenshot or a.save_pyvista:
        from .visualization import build_plotter,save_scene
        title=(f"ADAPT {adapt.observation_time} realization {adapt.realization}; "
               f"rss={a.rss:g}, nrho={a.nrho}; seeds={a.surface_spacing_deg:g}/{a.outer_spacing_deg:g} deg")
        if a.save_pyvista: save_scene(unique,a.save_pyvista)
        if a.plot or a.save_screenshot:
            plotter=build_plotter(adapt.map,unique,a.rss,a.map_clip_gauss,a.sphere_resolution,
                                  a.off_screen,a.show_source_surface,title,not a.no_orientation_triad,
                                  a.orientation_diagnostic,
                                  show_photosphere=not a.field_lines_only)
            if a.save_screenshot: plotter.show(screenshot=str(a.save_screenshot),auto_close=not a.plot)
            elif a.plot: plotter.show()
    summary={"ADAPT timestamp":adapt.observation_time,"ADAPT realization":adapt.realization,
             "PFSS grid":f"nrho={a.nrho}, rss={a.rss}","Surface seeds":ns,"Source-surface seeds":no,
             "Successful traces":len(resolved),"Closed unique lines":counts["closed"],
             "Positive open unique lines":counts["open_positive"],"Negative open unique lines":counts["open_negative"],
             "Unresolved traces":sum(r.classification=="unresolved" for r in all_records),
             "Duplicate traces removed":duplicate_count}
    for cls,label in (("open_negative","Blue"),("closed","Green"),("open_positive","Red")):
        if cls in vstats: summary[f"{label} VLA polylines/vertices"]=f"{vstats[cls].polylines}/{vstats[cls].vertices}"
    summary["Output directory"]=str(a.output_dir.resolve())
    (a.output_dir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    for k,v in summary.items(): LOG.info("%s: %s",k,v)
    return 0

def _save_results(path, records, metadata, overwrite):
    import numpy as np, tempfile
    path=Path(path)
    if path.exists() and not overwrite: raise FileExistsError(path)
    coords=[]; offsets=[0]; rows=[]
    for r in records:
        coords.append(r.coordinates); offsets.append(offsets[-1]+len(r.coordinates)); rows.append(r.metadata())
    fd,tmp=tempfile.mkstemp(prefix=path.name+".",suffix=".tmp",dir=path.parent); os.close(fd)
    try:
        with open(tmp,"wb") as f:
            np.savez_compressed(f,coordinates=np.concatenate(coords) if coords else np.empty((0,3)),
                                offsets=np.array(offsets),records=np.array(json.dumps(rows)),
                                model_metadata=np.array(json.dumps(metadata)))
            f.flush(); os.fsync(f.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)

def main(argv=None):
    a=parser().parse_args(argv)
    logging.basicConfig(level=getattr(logging,a.log_level),format="%(asctime)s %(levelname)s %(message)s")
    try: return run(a)
    except (ValueError,RuntimeError,FileExistsError) as e:
        LOG.error("%s",e); return 2
