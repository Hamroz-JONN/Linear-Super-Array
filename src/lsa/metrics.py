"""Performance metrics: beampattern, white-noise gain (WNG) and directivity factor (DF).

WNG (EUSIPCO Eq. 7, taken literally):   WNG = |d_s^H h|^2 / (h^H h),   reported as 10 log10(WNG) dB.
DF:  DF = |d_s^H h|^2 / ( (1/4pi) * integral over the full sphere of |d^H h|^2 dOmega ),   reported in dB.

Both divide by the actual look-direction response |d_s^H h|^2 instead of assuming it equals one, so a
design that violates the distortionless constraint is penalised rather than hidden.
"""

from __future__ import annotations

import numpy as np

from .array import Array
from .steering import C0, steering_vector


def beampattern(array: Array, freq_hz: float, h: np.ndarray, theta, phi=np.pi / 2, c: float = C0) -> np.ndarray:
    """B = d^H h, complex, with the shape of ``broadcast(theta, phi)``."""
    return steering_vector(array, freq_hz, theta, phi, c).conj() @ h


def wng_db(array: Array, freq_hz: float, h: np.ndarray, theta_s_deg: float = 0.0, c: float = C0) -> float:
    b = beampattern(array, freq_hz, h, np.radians(theta_s_deg), np.pi / 2, c)
    return float(10.0 * np.log10(abs(b) ** 2 / np.real(np.vdot(h, h))))


def sphere_quadrature(n_theta: int = 360, n_phi: int = 100):
    """Full-sphere quadrature: uniform in azimuth, Gauss-Legendre in cos(phi).

    Returns flattened (theta, phi, weights) with ``weights.sum() == 1`` (so the sphere *average* is a plain
    weighted sum). Converged to better than 1e-5 dB for this problem; see tests/test_verification.py.
    """
    theta = np.linspace(0.0, 2.0 * np.pi, n_theta, endpoint=False)
    u, wu = np.polynomial.legendre.leggauss(n_phi)
    phi = np.arccos(u)
    w = np.outer(np.full(n_theta, 1.0 / n_theta), wu / 2.0)
    T, P = np.meshgrid(theta, phi, indexing="ij")
    return T.ravel(), P.ravel(), w.ravel()


def legacy_grid(n_theta: int = 72, n_phi: int = 36):
    """The 72 x 36 grid of the original script: uniform azimuth, trapezoid rule in phi (poles included)."""
    theta = np.linspace(0.0, 2.0 * np.pi, n_theta, endpoint=False)
    phi = np.linspace(0.0, np.pi, n_phi)
    coeff = np.ones(n_phi)
    coeff[0] = coeff[-1] = 0.5
    wphi = np.sin(phi) * coeff * (np.pi / (n_phi - 1))
    w = np.outer(np.full(n_theta, 2.0 * np.pi / n_theta), wphi) / (4.0 * np.pi)
    T, P = np.meshgrid(theta, phi, indexing="ij")
    return T.ravel(), P.ravel(), w.ravel()


_DEFAULT_GRID = None


def df_db(array: Array, freq_hz: float, h: np.ndarray, theta_s_deg: float = 0.0, c: float = C0, grid=None) -> float:
    global _DEFAULT_GRID
    if grid is None:
        if _DEFAULT_GRID is None:
            _DEFAULT_GRID = sphere_quadrature()
        grid = _DEFAULT_GRID
    th, ph, w = grid
    b_s = beampattern(array, freq_hz, h, np.radians(theta_s_deg), np.pi / 2, c)
    avg = np.sum(w * np.abs(beampattern(array, freq_hz, h, th, ph, c)) ** 2)
    return float(10.0 * np.log10(abs(b_s) ** 2 / avg))
