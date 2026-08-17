"""PFSS construction against installed sunkit-magex."""
from __future__ import annotations

def calculate_pfss(adapt_map, nrho=60, rss=2.5):
    from sunkit_magex import pfss
    # Current ADAPT products are native 1-degree CAR maps.  The maintained
    # solver requires equal-area CEA input, so use its documented WCS-aware
    # reprojection helper (no manual transpose/reversal/roll).
    if pfss.utils.is_car_map(adapt_map):
        adapt_map = pfss.utils.car_to_cea(adapt_map, method="interp")
    # Installed sunkit-magex 1.1.0 calls this parameter ``nr`` (the public
    # Output grid still exposes it as the radial/log-rho grid).
    pfss_input = pfss.Input(adapt_map, nr=nrho, rss=rss)
    return pfss.pfss(pfss_input)

def make_tracer(name="performance", step_size=0.5, max_steps="auto"):
    from sunkit_magex.pfss import tracing
    if name == "performance":
        return tracing.PerformanceTracer(step_size=step_size, max_steps=max_steps)
    # sunkit-magex 1.1 PythonTracer uses scipy.solve_ivp and exposes tolerances
    # only; it always integrates fully in both directions.
    return tracing.PythonTracer()

def trace_field_lines(output, tracer, seeds):
    # Both maintained tracers already integrate both directions and return full lines.
    return tracer.trace(seeds, output)
