"""Array geometry and microphone types.

Indexing: the documentation uses one-based microphone indices m = 1..7. Code uses zero-based arrays,
so ``array.x[0]`` is microphone m = 1.

Directivity parameter p_m: ``p = 1`` is omnidirectional, ``p = 0`` is a pure dipole (bidirectional).
The response of microphone m is  g_m(theta, phi) = p_m + (1 - p_m) * cos(theta - alpha_m) * sin(phi).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SPACING_M = 0.005          # 0.5 cm between neighbouring microphones (EUSIPCO Sec. IV)
N_MICS = 7
ALPHA_DEFAULT = np.pi / 2  # all directional microphones face broadside (EUSIPCO Sec. IV)


@dataclass(frozen=True)
class Array:
    """A linear array along the x-axis."""

    name: str
    x: np.ndarray       # microphone positions in metres, shape (M,)
    p: np.ndarray       # directivity parameters, shape (M,)
    alpha: np.ndarray   # orientations in radians, shape (M,)

    def __post_init__(self):
        if not (self.x.shape == self.p.shape == self.alpha.shape and self.x.ndim == 1):
            raise ValueError("x, p and alpha must be 1-D arrays of equal length")
        if np.any(self.p < 0) or np.any(self.p > 1):
            raise ValueError("p must lie in [0, 1]")

    @property
    def M(self) -> int:
        return self.x.size

    @property
    def is_omni(self) -> np.ndarray:
        return self.p == 1.0

    @property
    def n_omni(self) -> int:
        return int(self.is_omni.sum())

    @property
    def n_bidirectional(self) -> int:
        return int((self.p == 0.0).sum())

    @property
    def aperture_m(self) -> float:
        return float(self.x.max() - self.x.min())

    def centered(self) -> "Array":
        """Same array with its midpoint moved to the origin (needed by the Jacobi-Anger design)."""
        shift = 0.5 * (self.x.max() + self.x.min())
        return Array(self.name + " (centred)", self.x - shift, self.p, self.alpha)

    def is_centered(self, tol: float = 1e-12) -> bool:
        return abs(0.5 * (self.x.max() + self.x.min())) < tol

    def table(self) -> str:
        """Plain-text table, one-based indices."""
        rows = ["  m | x (cm) | type          | p_m | alpha (deg)"]
        for i in range(self.M):
            kind = "omni" if self.p[i] == 1 else ("bidirectional" if self.p[i] == 0 else "first-order")
            alpha = "n/a" if self.p[i] == 1 else f"{np.degrees(self.alpha[i]):.0f}"
            rows.append(f"  {i + 1} | {self.x[i] * 100:6.2f} | {kind:13s} | {self.p[i]:3.0f} | {alpha}")
        return "\n".join(rows)


def make_array(p, name: str = "custom", spacing: float = SPACING_M, alpha: float = ALPHA_DEFAULT) -> Array:
    """Uniform linear array: microphone m (one-based) sits at x = (m - 1) * spacing."""
    p = np.asarray(p, dtype=float)
    return Array(
        name=name,
        x=np.arange(p.size) * spacing,
        p=p,
        alpha=np.full(p.size, alpha),
    )


# documented: bidirectional at one-based positions 1,3,5,7 and omni at 2,4,6  -> 3 omni / 4 bidirectional
#             (confirmed by a co-author of the EUSIPCO paper)
# alternative: omni at one-based positions 1,3,5,7 -> 4 omni / 3 bidirectional
#             (the assignment that reproduces the published curves; this is also the structure of the
#              2023 letter's array: omni at both ends)
PRESETS = {
    "documented": make_array([0, 1, 0, 1, 0, 1, 0], name="documented (3 omni / 4 bidirectional)"),
    "alternative": make_array([1, 0, 1, 0, 1, 0, 1], name="alternative (4 omni / 3 bidirectional)"),
}
