#!/usr/bin/env python3
"""Save figures to figures/ : polar beampattern at 1 kHz and WNG/DF versus frequency."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

from lsa import PRESETS, df_db, null_constrained_min_norm, wng_db  # noqa: E402
from lsa.metrics import beampattern  # noqa: E402

out = ROOT / "figures"
out.mkdir(exist_ok=True)

# polar beampattern, 1 kHz
th = np.linspace(-np.pi, np.pi, 721)
fig = plt.figure(figsize=(5, 5))
ax = fig.add_subplot(projection="polar")
for key, arr in PRESETS.items():
    h = null_constrained_min_norm(arr, 1000.0)
    b = 20 * np.log10(np.abs(beampattern(arr, 1000.0, h, th)) + 1e-12)
    ax.plot(th, np.maximum(b, -40), label=key)
ax.set_rlim(-40, 0)
ax.set_title("Beampattern at 1 kHz (dB)")
ax.legend(loc="lower left", bbox_to_anchor=(0.9, 0.0))
fig.savefig(out / "beampattern_1khz.png", dpi=150, bbox_inches="tight")

# WNG and DF versus frequency
freqs = np.linspace(100, 4000, 40)
fig, axs = plt.subplots(1, 2, figsize=(10, 4))
for key, arr in PRESETS.items():
    hs = [null_constrained_min_norm(arr, f) for f in freqs]
    axs[0].plot(freqs, [wng_db(arr, f, h) for f, h in zip(freqs, hs)], label=key)
    axs[1].plot(freqs, [df_db(arr, f, h) for f, h in zip(freqs, hs)], label=key)
axs[0].set(xlabel="Frequency (Hz)", ylabel="WNG (dB)", title="White-noise gain")
axs[1].set(xlabel="Frequency (Hz)", ylabel="DF (dB)", title="Directivity factor")
for a in axs:
    a.grid(alpha=0.3)
axs[0].legend()
fig.tight_layout()
fig.savefig(out / "wng_df_vs_frequency.png", dpi=150)
print("saved", *(p.name for p in sorted(out.glob("*.png"))))
