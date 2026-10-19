"""Beamformer designs.

Headline method: ``null_constrained_min_norm`` -- the exact design used for every number in the paper.
Cross-check:     ``jacobi_anger`` -- the closed-form-target design of the 2023 letter (Luo et al.).

Both return a complex weight vector ``h`` of shape (M,), to be used with ``B(theta, phi) = d(theta, phi)^H h``.
"""

from __future__ import annotations

import numpy as np
from scipy.special import jv

from .array import Array
from .steering import C0, PHASE_SIGN, steering_vector

# Second-order supercardioid target of the 2023 letter: B(theta) = a0 + a1 cos(theta) + a2 cos(2 theta)
SUPERCARDIOID_ALPHA = (0.309, 0.484, 0.207)


def constraint_directions_deg(theta_s_deg: float = 0.0, null_offsets_deg=(106.0, 153.0)) -> np.ndarray:
    """[look, +n1, -n1, +n2, -n2] relative to the look direction (degrees)."""
    out = [theta_s_deg]
    for n in null_offsets_deg:
        out += [theta_s_deg + n, theta_s_deg - n]
    return np.array(out, dtype=float)


def null_constrained_min_norm(array: Array, freq_hz: float, theta_s_deg: float = 0.0,
                              null_offsets_deg=(106.0, 153.0), c: float = C0, rcond: float = 1e-12) -> np.ndarray:
    """Minimum-norm solution of  D h = e1,  rows of D = d(theta_i)^H at the look direction and the null directions.

    ``rcond=1e-12`` matches the original script (``torch.linalg.pinv(D, rcond=1e-12)``).
    """
    dirs = np.radians(constraint_directions_deg(theta_s_deg, null_offsets_deg))
    D = steering_vector(array, freq_hz, dirs, np.pi / 2, c).conj()      # (n_constraints, M)
    rhs = np.zeros(D.shape[0], dtype=complex)
    rhs[0] = 1.0
    return np.linalg.pinv(D, rcond=rcond) @ rhs


def jacobi_anger(array: Array, freq_hz: float, theta_s_deg: float = 0.0, c: float = C0,
                 alpha=SUPERCARDIOID_ALPHA) -> np.ndarray:
    """Jacobi-Anger design of the 2023 letter, end-fire only, using the omnidirectional microphones.

    The beampattern is expanded in cos(n*theta) with Bessel-function coefficients anchored at the array
    centre, so the array **must be centred**: pass ``array.centered()``. Bidirectional weights are zero,
    because the target is symmetric about the end-fire axis (see docs/PITFALLS.md, pitfall 4).
    """
    if theta_s_deg != 0.0:
        raise NotImplementedError("Only the end-fire look direction (theta_s = 0) is implemented.")
    if not array.is_centered():
        raise ValueError("jacobi_anger needs a centred array (its series is anchored at the origin). "
                         "Pass array.centered().")
    N = len(alpha) - 1
    omni = array.is_omni
    if omni.sum() < N + 1:
        raise ValueError(f"Need at least {N + 1} omnidirectional microphones, got {int(omni.sum())}.")
    mu = 2.0 * np.pi * freq_hz * array.x[omni] / c
    n = np.arange(N + 1)[:, None]
    theta_mat = ((-1j * PHASE_SIGN) ** n) * jv(n, mu[None, :])          # (N+1, n_omni)
    eta = np.array([alpha[0]] + [a / 2.0 for a in alpha[1:]], dtype=complex)
    h_omni = theta_mat.conj().T @ np.linalg.solve(theta_mat @ theta_mat.conj().T, eta)
    h = np.zeros(array.M, dtype=complex)
    h[omni] = h_omni
    return h
