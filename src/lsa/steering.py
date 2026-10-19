"""Steering vectors. The phase-sign convention is defined here, once.

d_m(theta, phi) = g_m(theta, phi) * exp(PHASE_SIGN * j * (2*pi*f/c) * x_m * cos(theta) * sin(phi))

with the directional response g_m = p_m + (1 - p_m) * cos(theta - alpha_m) * sin(phi).

PHASE_SIGN = -1 follows the EUSIPCO paper (Eq. 3 and 5) and the original script. The 2023 letter uses +1. The two
conventions are complex conjugates and give identical DF and WNG *provided design and evaluation use the same
one*. Mixing them silently breaks the distortionless constraint (docs/PITFALLS.md, pitfall 1).
"""

from __future__ import annotations

import numpy as np

from .array import Array

C0 = 340.0          # speed of sound in m/s (the value used by the original script; see docs/CONVENTIONS.md)
PHASE_SIGN = -1


def steering_vector(array: Array, freq_hz: float, theta, phi=np.pi / 2, c: float = C0,
                    phase_sign: int = PHASE_SIGN) -> np.ndarray:
    """Return d with shape ``np.broadcast(theta, phi).shape + (M,)``; the beampattern is ``B = d^H h``."""
    theta, phi = np.broadcast_arrays(np.asarray(theta, dtype=float), np.asarray(phi, dtype=float))
    th = theta[..., None]
    ph = phi[..., None]
    k = 2.0 * np.pi * freq_hz / c
    phase = np.exp(phase_sign * 1j * k * array.x * np.cos(th) * np.sin(ph))
    gain = array.p + (1.0 - array.p) * np.cos(th - array.alpha) * np.sin(ph)
    return gain * phase
