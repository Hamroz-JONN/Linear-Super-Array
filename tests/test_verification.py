"""Verification tests. Run with:  pytest -q"""

import csv
from pathlib import Path

import numpy as np
import pytest

from lsa import (PRESETS, df_db, jacobi_anger, make_array, null_constrained_min_norm, steering_vector, wng_db)
from lsa.beamformers import constraint_directions_deg
from lsa.metrics import beampattern, legacy_grid, sphere_quadrature
from lsa.reference import ORIGINAL_DF_ALT_DB, ORIGINAL_FREQS_HZ, ORIGINAL_WNG_ALT_DB

FREQS = ORIGINAL_FREQS_HZ
DOC, ALT = PRESETS["documented"], PRESETS["alternative"]
ROOT = Path(__file__).resolve().parents[1]


def test_geometry():
    for arr, counts in ((DOC, (3, 4)), (ALT, (4, 3))):
        assert arr.M == 7
        assert np.allclose(np.diff(arr.x), 0.005)
        assert abs(arr.aperture_m - 0.03) < 1e-12
        assert (arr.n_omni, arr.n_bidirectional) == counts


def test_documented_is_odd_one_based_bidirectional():
    # one-based positions 1,3,5,7 are bidirectional (p = 0)
    assert [i + 1 for i in np.flatnonzero(DOC.p == 0)] == [1, 3, 5, 7]


@pytest.mark.parametrize("arr", [DOC, ALT])
@pytest.mark.parametrize("f", FREQS)
def test_distortionless_and_nulls(arr, f):
    h = null_constrained_min_norm(arr, f)
    B = beampattern(arr, f, h, np.radians(constraint_directions_deg()))
    assert abs(B[0] - 1) < 1e-10
    assert np.max(np.abs(B[1:])) < 1e-10


@pytest.mark.parametrize("f", FREQS)
def test_bidirectional_weights_vanish_for_documented_array(f):
    h = null_constrained_min_norm(DOC, f)
    assert np.max(np.abs(h[~DOC.is_omni])) < 1e-8


def test_wrong_phase_sign_breaks_distortionless_response():
    f = 1000.0
    h = null_constrained_min_norm(DOC, f)                      # designed with PHASE_SIGN = -1
    d_wrong = steering_vector(DOC, f, 0.0, phase_sign=+1)      # evaluated with the opposite sign
    assert abs(np.vdot(d_wrong, h) - 1) > 0.5


def test_exact_design_is_origin_invariant():
    shifted = make_array([0, 1, 0, 1, 0, 1, 0])
    shifted = type(shifted)(shifted.name, shifted.x + 0.123, shifted.p, shifted.alpha)
    for f in FREQS:
        a = null_constrained_min_norm(DOC, f)
        b = null_constrained_min_norm(shifted, f)
        assert abs(wng_db(DOC, f, a) - wng_db(shifted, f, b)) < 1e-6
        assert abs(df_db(DOC, f, a) - df_db(shifted, f, b)) < 1e-6


def test_jacobi_anger_requires_centred_array():
    with pytest.raises(ValueError):
        jacobi_anger(DOC, 1000.0)
    with pytest.raises(NotImplementedError):
        jacobi_anger(DOC.centered(), 1000.0, theta_s_deg=30.0)


def test_jacobi_anger_matches_exact_design():
    arr = DOC.centered()
    for f in FREQS:
        h_ja = jacobi_anger(arr, f)
        h_ex = null_constrained_min_norm(DOC, f)
        assert abs(beampattern(arr, f, h_ja, 0.0) - 1) < 0.02            # approximately distortionless
        assert abs(wng_db(arr, f, h_ja) - wng_db(DOC, f, h_ex)) < 0.2
        assert abs(df_db(arr, f, h_ja) - df_db(DOC, f, h_ex)) < 0.07


def test_df_grid_convergence():
    for f in (500.0, 2000.0, 3500.0):
        h = null_constrained_min_norm(DOC, f)
        ref = df_db(DOC, f, h, grid=sphere_quadrature(720, 200))
        assert abs(df_db(DOC, f, h) - ref) < 1e-5
        assert abs(df_db(DOC, f, h, grid=legacy_grid()) - ref) < 1e-3     # original 72 x 36 grid


def test_sanity_directivity_values():
    omni = make_array([1, 1, 1])
    h = np.array([0, 1, 0], dtype=complex)
    assert abs(df_db(omni, 1000.0, h)) < 1e-6                              # a single omni has DF = 0 dB
    dipole = make_array([0])
    assert abs(df_db(dipole, 1000.0, np.array([1.0 + 0j]), theta_s_deg=90.0) - 10 * np.log10(3)) < 1e-4  # 4.771 dB


def test_port_reproduces_original_script_results():
    for f, w_ref, d_ref in zip(FREQS, ORIGINAL_WNG_ALT_DB, ORIGINAL_DF_ALT_DB):
        h = null_constrained_min_norm(ALT, f)
        assert abs(wng_db(ALT, f, h) - w_ref) < 0.006
        assert abs(df_db(ALT, f, h) - d_ref) < 0.0006


def test_regression_against_expected_results():
    with (ROOT / "data" / "expected_results.csv").open() as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 21
    for r in rows:
        f = float(r["frequency_hz"])
        if r["design"] == "exact":
            arr = PRESETS[r["array"]]
            h = null_constrained_min_norm(arr, f)
        else:
            arr = PRESETS[r["array"]].centered()
            h = jacobi_anger(arr, f)
        assert abs(wng_db(arr, f, h) - float(r["wng_db"])) < 1e-3
        assert abs(df_db(arr, f, h) - float(r["df_db"])) < 1e-3
