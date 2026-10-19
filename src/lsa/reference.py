"""Digitised reference curves (EUSIPCO Fig. 6, LSA at 0 deg), the original script's results, and the MAE metric.

The CSV ``data/reference_digitized.csv`` is a template until populated. ``load_reference`` returns ``None`` when
it holds no data rows, so nothing downstream ever invents reference values.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
REFERENCE_CSV = DATA_DIR / "reference_digitized.csv"

# Values reported in the OJSS reproduction paper (Eq. 39 and 41) for the ALTERNATIVE array, produced by the original
# PyTorch script. They validate this NumPy port against that script. They are NOT values from the EUSIPCO paper,
# which tabulates none.
ORIGINAL_FREQS_HZ = (500, 1000, 1500, 2000, 2500, 3000, 3500)
ORIGINAL_WNG_ALT_DB = (-33.76, -21.81, -14.92, -10.14, -6.55, -3.74, -1.48)
ORIGINAL_DF_ALT_DB = (8.206, 8.178, 8.132, 8.067, 7.982, 7.876, 7.748)


def load_reference(path: Path = REFERENCE_CSV, array: str | None = None):
    """Return ``{'frequency_hz', 'wng_db', 'df_db'}`` numpy arrays, or ``None`` if the file has no data rows."""
    path = Path(path)
    if not path.exists():
        return None
    with path.open(newline="") as fh:
        rows = [r for r in csv.DictReader(line for line in fh if not line.lstrip().startswith("#")) if r.get("frequency_hz")]
    if array is not None:
        rows = [r for r in rows if r.get("array") == array]
    if not rows:
        return None
    rows.sort(key=lambda r: float(r["frequency_hz"]))
    return {
        "frequency_hz": np.array([float(r["frequency_hz"]) for r in rows]),
        "wng_db": np.array([float(r["wng_db"]) if r["wng_db"] else np.nan for r in rows]),
        "df_db": np.array([float(r["df_db"]) if r["df_db"] else np.nan for r in rows]),
    }


def mae(a, b) -> float:
    """Mean absolute error in dB, ignoring NaNs."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.nanmean(np.abs(a - b)))
