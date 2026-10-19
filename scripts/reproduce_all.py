#!/usr/bin/env python3
"""Reproduce every number in the repository and check it.

    python scripts/reproduce_all.py                  # run all checks, exit non-zero on failure
    python scripts/reproduce_all.py --write-expected # regenerate data/expected_results.csv

What it does, in order:
  1. prints the two array configurations (one-based indices)
  2. verifies the designs (distortionless response, nulls, geometry, bidirectional weights)
  3. prints DF and WNG for the documented array (headline), the alternative array, and the Jacobi-Anger cross-check
  4. compares against data/expected_results.csv (regression, 1e-3 dB)
  5. validates the port: alternative array vs the original script's results (OJSS paper Eq. 39 and 41)
  6. if data/reference_digitized.csv has data, reports the mean absolute errors reported in the paper
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402

from lsa import PRESETS, df_db, jacobi_anger, null_constrained_min_norm, wng_db  # noqa: E402
from lsa.beamformers import constraint_directions_deg  # noqa: E402
from lsa.metrics import beampattern  # noqa: E402
from lsa.reference import (ORIGINAL_DF_ALT_DB, ORIGINAL_FREQS_HZ, ORIGINAL_WNG_ALT_DB, load_reference, mae)  # noqa: E402

FREQS = ORIGINAL_FREQS_HZ
EXPECTED_CSV = ROOT / "data" / "expected_results.csv"
REGRESSION_TOL_DB = 1e-3
ORIG_TOL_WNG_DB = 0.006
ORIG_TOL_DF_DB = 0.0005

failures: list[str] = []


def check(ok: bool, msg: str) -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {msg}")
    if not ok:
        failures.append(msg)


def compute() -> dict[tuple[str, str], list[tuple[float, float, float]]]:
    """{(array, design): [(f, DF_dB, WNG_dB), ...]}"""
    out = {}
    for key in ("documented", "alternative"):
        arr = PRESETS[key]
        out[(key, "exact")] = []
        for f in FREQS:
            h = null_constrained_min_norm(arr, f)
            out[(key, "exact")].append((f, df_db(arr, f, h), wng_db(arr, f, h)))
    arr = PRESETS["documented"].centered()
    out[("documented", "jacobi_anger")] = []
    for f in FREQS:
        h = jacobi_anger(arr, f)
        out[("documented", "jacobi_anger")].append((f, df_db(arr, f, h), wng_db(arr, f, h)))
    return out


def print_table(title: str, rows) -> None:
    print(f"\n{title}")
    print("  freq (Hz) |  DF (dB) | WNG (dB)")
    for f, d, w in rows:
        print(f"  {f:9.0f} | {d:8.3f} | {w:8.3f}")


def write_expected(results) -> None:
    EXPECTED_CSV.parent.mkdir(exist_ok=True)
    with EXPECTED_CSV.open("w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(["array", "design", "frequency_hz", "df_db", "wng_db"])
        for (a, d), rows in results.items():
            for f, df, wng in rows:
                wr.writerow([a, d, int(f), f"{df:.4f}", f"{wng:.4f}"])
    print(f"wrote {EXPECTED_CSV.relative_to(ROOT)}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write-expected", action="store_true")
    args = ap.parse_args()

    results = compute()
    if args.write_expected:
        write_expected(results)
        return 0

    print("=" * 70 + "\n1. Array configurations (one-based microphone index m)\n" + "=" * 70)
    for key, arr in PRESETS.items():
        print(f"\n{arr.name}  [p = {arr.p.astype(int).tolist()}]")
        print(arr.table())

    print("\n" + "=" * 70 + "\n2. Verification of the designs (exact design, 500-3500 Hz)\n" + "=" * 70)
    for key, arr in PRESETS.items():
        print(f"\n{key}:")
        check(arr.M == 7 and abs(arr.aperture_m - 0.03) < 1e-12, "7 microphones, 3 cm aperture")
        check(np.allclose(np.diff(arr.x), 0.005), "0.5 cm spacing")
        check((arr.n_omni, arr.n_bidirectional) == ((3, 4) if key == "documented" else (4, 3)),
              f"{arr.n_omni} omni / {arr.n_bidirectional} bidirectional")
        worst_look, worst_null, worst_bidir = 0.0, 0.0, 0.0
        for f in FREQS:
            h = null_constrained_min_norm(arr, f)
            dirs = np.radians(constraint_directions_deg())
            B = beampattern(arr, f, h, dirs)
            worst_look = max(worst_look, abs(B[0] - 1))
            worst_null = max(worst_null, np.max(np.abs(B[1:])))
            if key == "documented":
                worst_bidir = max(worst_bidir, np.max(np.abs(h[~arr.is_omni])))
        check(worst_look < 1e-10, f"distortionless: max |B(0 deg) - 1| = {worst_look:.1e}")
        check(worst_null < 1e-10, f"nulls at +-106, +-153 deg: max |B| = {worst_null:.1e}")
        if key == "documented":
            check(worst_bidir < 1e-8, f"bidirectional weights are zero: max |h_bidir| = {worst_bidir:.1e}")

    print("\n" + "=" * 70 + "\n3. Results (c = 340 m/s, end-fire look direction)\n" + "=" * 70)
    print_table("DOCUMENTED array (3 omni / 4 bidirectional), exact design  <- headline", results[("documented", "exact")])
    print_table("ALTERNATIVE array (4 omni / 3 bidirectional), exact design", results[("alternative", "exact")])
    print_table("Cross-check: DOCUMENTED array, Jacobi-Anger design (array centred)", results[("documented", "jacobi_anger")])
    dw = max(abs(a[2] - b[2]) for a, b in zip(results[("documented", "exact")], results[("documented", "jacobi_anger")]))
    dd = max(abs(a[1] - b[1]) for a, b in zip(results[("documented", "exact")], results[("documented", "jacobi_anger")]))
    print(f"\n  exact vs Jacobi-Anger, largest difference: WNG {dw:.3f} dB, DF {dd:.3f} dB")

    print("\n" + "=" * 70 + "\n4. Regression against data/expected_results.csv\n" + "=" * 70)
    if not EXPECTED_CSV.exists():
        check(False, "data/expected_results.csv is missing (run with --write-expected)")
    else:
        with EXPECTED_CSV.open() as fh:
            exp = list(csv.DictReader(fh))
        worst = 0.0
        for r in exp:
            rows = results[(r["array"], r["design"])]
            f, df, wng = next(x for x in rows if x[0] == float(r["frequency_hz"]))
            worst = max(worst, abs(df - float(r["df_db"])), abs(wng - float(r["wng_db"])))
        check(len(exp) == 21 and worst < REGRESSION_TOL_DB, f"{len(exp)} rows, largest deviation {worst:.1e} dB")

    print("\n" + "=" * 70 + "\n5. Port validation: alternative array vs the original script's results (reported in the OJSS paper, Eq. 39, 41)\n" + "=" * 70)
    alt = results[("alternative", "exact")]
    ew = max(abs(r[2] - p) for r, p in zip(alt, ORIGINAL_WNG_ALT_DB))
    ed = max(abs(r[1] - p) for r, p in zip(alt, ORIGINAL_DF_ALT_DB))
    check(ew < ORIG_TOL_WNG_DB, f"WNG: largest difference {ew:.4f} dB (tolerance {ORIG_TOL_WNG_DB})")
    check(ed < ORIG_TOL_DF_DB, f"DF:  largest difference {ed:.4f} dB (tolerance {ORIG_TOL_DF_DB})")

    print("\n" + "=" * 70 + "\n6. Digitised reference curve (data/reference_digitized.csv)\n" + "=" * 70)
    ref = load_reference()
    if ref is None:
        print("  no data rows in data/reference_digitized.csv -- skipped (see data/README.md)")
    else:
        for key in ("documented", "alternative"):
            rows = results[(key, "exact")]
            fr = {r[0]: r for r in rows}
            sel = [f for f in ref["frequency_hz"] if f in fr]
            w = [fr[f][2] for f in sel]
            d = [fr[f][1] for f in sel]
            idx = [list(ref["frequency_hz"]).index(f) for f in sel]
            print(f"  {key}: MAE_WNG = {mae(w, ref['wng_db'][idx]):.2f} dB, MAE_DF = {mae(d, ref['df_db'][idx]):.2f} dB "
                  f"({len(sel)} frequencies)")

    print("\n" + "=" * 70)
    if failures:
        print(f"{len(failures)} CHECK(S) FAILED")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
