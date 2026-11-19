"""Test 11b: Test 11 with the model trained, validated and scored on Queensland races only (19 Nov 2026, founder:
"What about just QLD"). Same script (bw_bsp_sect.py) with QLD_ONLY set."""
import os, sys

os.environ["QLD_ONLY"] = "1"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bw_bsp_sect import main

if __name__ == "__main__":
    main(*sys.argv[1:4])
