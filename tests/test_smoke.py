import json
import pytest
from spac_viz.cli import main

@pytest.mark.integration
def test_coarse_end_to_end(synthetic_adapt,tmp_path):
    out=tmp_path/"out"
    rc=main(["--adapt-file",str(synthetic_adapt),"--realization","0","--output-dir",str(out),
             "--surface-spacing-deg","90","--outer-spacing-deg","90",
             "--outer-seeds",
             "--theta-min-deg","30","--theta-max-deg","150",
             "--phi-min-deg","0","--phi-max-deg","270",
             "--nrho","8","--trace-chunk-size","8","--sphere-resolution","30",
             "--export-vla","--overwrite"])
    assert rc==0
    summary=json.loads((out/"summary.json").read_text())
    assert summary["Surface seeds"]==8 and summary["Source-surface seeds"]==8
    assert sum(summary[k] for k in ("Closed unique lines","Positive open unique lines",
                                    "Negative open unique lines"))>=1
    assert (out/"trace_results.npz").exists()

@pytest.mark.network
@pytest.mark.skipif(not __import__("os").environ.get("RUN_NETWORK_TESTS"),reason="set RUN_NETWORK_TESTS=1")
def test_download_network(tmp_path):
    from spac_viz.adapt import download_adapt
    assert download_adapt(tmp_path,time="2024-01-01T00:00:00").exists()
