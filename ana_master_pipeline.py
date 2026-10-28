"""
Ambient Nursing Ally (ANA) — Root Entrypoint
Delegates execution directly to main/ana_master_pipeline.py
"""

import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from main.ana_master_pipeline import (
    ANAPipelineState,
    build_ana_master_graph,
    run_ana_master_pipeline,
    run_comprehensive_demo
)

if __name__ == "__main__":
    run_comprehensive_demo()
