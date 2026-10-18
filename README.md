# LSA Beamformer Reproduction

[![DOI](https://img.shields.io/badge/paper-DOI%2010.65161-blue)](https://doi.org/10.65161/recC6aX4oKVBJEXdP)
<!-- Add after enabling CI:  ![tests](https://github.com/<your-username>/lsa-beamformer-reproduction/actions/workflows/ci.yml/badge.svg) -->

**Quick links:** [Quickstart](#quickstart) · [The array](#the-array) · [What the code does](#what-the-code-does) · [Status](#status) · [Citation](#citation-and-license)

---

## Summary

An independent, fully documented Python implementation of the conventional mixed-directivity linear superarray (LSA) beamformer from Huang and Habets (EUSIPCO 2025), which combines omnidirectional and bidirectional microphones in a 3 cm array. It was written so that nobody else has to reverse-engineer the design: every convention and judgment call is documented, and one command reproduces the results.

**Paper:** [Independent Reproduction of a Mixed-Directivity Linear Superarray Beamformer: Evidence of a Microphone-Configuration Inconsistency](https://doi.org/10.65161/recC6aX4oKVBJEXdP), *The Oxford Journal of Student Scholarship*, Vol. 11, Issue 7 (2026). DOI: [`10.65161/recC6aX4oKVBJEXdP`](https://doi.org/10.65161/recC6aX4oKVBJEXdP)

---

## Quickstart

**1. Clone**

```bash
git clone https://github.com/<your-username>/lsa-beamformer-reproduction.git
cd lsa-beamformer-reproduction
```

**2. Install** (Python 3.9 or newer)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**3. Run**

```bash
python scripts/reproduce_all.py
```

**4. Expected output**

The script verifies the beamformer, then prints Directivity Factor (DF) and White Noise Gain (WNG) at the seven evaluation frequencies:

```
  f (Hz) |   DF (dB) |   WNG (dB)
-----------------------------------
     500 |     8.210 |    -41.663
    1000 |     8.201 |    -29.671
    1500 |     8.187 |    -22.707
    2000 |     8.167 |    -17.821
    2500 |     8.140 |    -14.087
    3000 |     8.108 |    -11.090
    3500 |     8.069 |     -8.611
```

These numbers are also stored in [`data/expected_results.csv`](data/expected_results.csv). If your output differs by more than rounding, see [`docs/PITFALLS.md`](docs/PITFALLS.md).

To run the automated checks:

```bash
pytest tests/
```

---

## The array

> **Indexing is one-based throughout this repository.** Microphone 1 is at the left end of the array and microphone 7 is at the right end.
>
> **The array is 3 omnidirectional + 4 bidirectional microphones**, interleaved, with bidirectional microphones at the odd positions (1, 3, 5, 7) and omnidirectional microphones at the even positions (2, 4, 6).

| Index *m* | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| **Position** (cm from mic 1) | 0.0 | 0.5 | 1.0 | 1.5 | 2.0 | 2.5 | 3.0 |
| **Type** | bidirectional | omni | bidirectional | omni | bidirectional | omni | bidirectional |
| **Directivity parameter** `p_m` | 0 | 1 | 0 | 1 | 0 | 1 | 0 |
| **Orientation** `α_m` | 90° | n/a | 90° | n/a | 90° | n/a | 90° |

- Spacing is 0.5 cm between neighbouring microphones, giving a 3 cm aperture.
- `p_m = 1` is omnidirectional and `p_m = 0` is a pure dipole. The response is `g_m(θ, φ) = p_m + (1 − p_m)·cos(θ − α_m)·sin φ`.
- The code centres the array on the origin (positions −1.5 to +1.5 cm). This is a global phase shift and has no effect on DF or WNG.
- Look direction: θ = 0°, φ = 90° (end-fire). Prescribed nulls: ±106° and ±153° in the horizontal plane.

Every convention behind these choices is listed with its source in [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

---

## What the code does

```
1. Geometry     src/lsa/array.py          →  microphone positions, types, and p_m (table above)
2. Steering     src/lsa/steering.py       →  3D steering vectors with one stated phase-sign convention
3. Design       src/lsa/beamformers.py    →  weights h(ω) from two methods: null-constrained minimum-norm
                                              and Jacobi–Anger series expansion
4. Metrics      src/lsa/metrics.py        →  3D spherical-average DF and distortionless WNG
5. Comparison   src/lsa/reference.py      →  results checked against digitized reference curves in data/
```

`scripts/reproduce_all.py` runs all five stages. `scripts/make_figures.py` regenerates the paper's figures.

---

## Status

**Verified:** the beamformer satisfies the distortionless constraint, places its nulls at the prescribed angles, and matches the published Directivity Factor to within about 0.1 dB. The original authors confirmed the 3 omni / 4 bidirectional configuration.

**Open:** the White Noise Gain still differs from the published curve by roughly 8 dB. The published paper attributes this to an odd-indexed-omni microphone assignment, but the authors' confirmed configuration contradicts that explanation, so the cause is unresolved.

Full details, including what was ruled out, are in [`docs/STATUS.md`](docs/STATUS.md).

---

## Citation and license

If you use this code, please cite the paper:

```bibtex
@article{qosimov2026lsa,
  author  = {Qosimov, Hamrozjon},
  title   = {Independent Reproduction of a Mixed-Directivity Linear Superarray
             Beamformer: Evidence of a Microphone-Configuration Inconsistency},
  journal = {The Oxford Journal of Student Scholarship},
  volume  = {11},
  number  = {7},
  year    = {2026},
  doi     = {10.65161/recC6aX4oKVBJEXdP}
}
```

The method reproduced here is described in: W. Huang and E. A. P. Habets, "Robust differential beamformers for linear superarrays with non-uniformly oriented directional microphones," *Proc. EUSIPCO*, 2025.

Released under the [MIT License](LICENSE).
