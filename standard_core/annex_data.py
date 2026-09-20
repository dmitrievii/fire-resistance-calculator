"""Annex materialization metadata for the current cumulative release.

Stage N1 materializes current-source Table Б.1 rolled-steel physical constants and
Tables В.3, В.4 and В.5 strength data. Other Annex Б/В/Г/И boundaries remain
explicitly external and are listed in data/annex_reconstruction_catalog_v0_27_stage_n1.json.
"""

from pathlib import Path

ANNEX_RECONSTRUCTION_CATALOG_PATH = Path(__file__).resolve().parents[1] / "data" / "annex_reconstruction_catalog_v0_27_stage_n1.json"
