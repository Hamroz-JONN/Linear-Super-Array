"""Conventional mixed-directivity linear superarray (LSA) beamformer: a documented reproduction.

Pipeline (see README):  array -> steering -> beamformers -> metrics -> reference comparison.

Conventions used throughout (details and sources in docs/CONVENTIONS.md):
  * one-based microphone indices in documentation, zero-based arrays in code
  * steering vector  d_m = g_m(theta, phi) * exp(-j * w * x_m * cos(theta) * sin(phi) / c)   (EUSIPCO Eq. 3 and 5)
  * beampattern      B = d^H h   (rows of the constraint matrix are d^H)
  * speed of sound   c = 340 m/s
"""

from .array import Array, PRESETS, make_array
from .beamformers import (
    SUPERCARDIOID_ALPHA,
    jacobi_anger,
    null_constrained_min_norm,
)
from .metrics import beampattern, df_db, sphere_quadrature, wng_db
from .steering import C0, PHASE_SIGN, steering_vector

__all__ = [
    "Array", "PRESETS", "make_array",
    "SUPERCARDIOID_ALPHA", "jacobi_anger", "null_constrained_min_norm",
    "beampattern", "df_db", "sphere_quadrature", "wng_db",
    "C0", "PHASE_SIGN", "steering_vector",
]
