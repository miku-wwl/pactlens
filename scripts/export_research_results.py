"""Export only a reviewed future formal-analysis artifact and hash-matched sources."""

import argparse
from pathlib import Path

from pactlens.research.reporting import export_results

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("artifact", type=Path)
    p.add_argument("output", type=Path)
    for key in ("locked_l2", "immutable_l4", "frozen_configuration", "thresholds"):
        p.add_argument("--" + key.replace("_", "-"), type=Path, required=True)
    p.add_argument("--charts", action="store_true")
    a = p.parse_args()
    sources = {
        k: getattr(a, k)
        for k in ("locked_l2", "immutable_l4", "frozen_configuration", "thresholds")
    }
    export_results(a.artifact, sources, a.output, charts=a.charts)
