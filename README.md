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

**2. Install** (Python 3.11 or newer)

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

The script prints both array configurations, verifies the designs, then prints Directivity Factor (DF) and White Noise Gain (WNG) at the seven evaluation frequencies and ends with `ALL CHECKS PASSED`. The headline result is the **documented** 3 omni / 4 bidirectional array with the exact null-constrained design (c = 340 m/s):

```
  freq (Hz) |  DF (dB) | WNG (dB)
        500 |    8.211 |  -41.520
       1000 |    8.198 |  -29.520
       1500 |    8.176 |  -22.545
       2000 |    8.146 |  -17.645
       2500 |    8.107 |  -13.893
       3000 |    8.059 |  -10.879
       3500 |    8.001 |   -8.384
```

It also prints the 4 omni / 3 bidirectional *alternative* array (WNG −33.756 dB at 500 Hz) and a Jacobi–Anger cross-check, which agrees with the exact design to within 0.18 dB WNG and 0.065 dB DF. All values are stored in [`data/expected_results.csv`](data/expected_results.csv). If your output differs by more than rounding, see [`docs/PITFALLS.md`](docs/PITFALLS.md).

To run the automated checks:

```bash
pytest -q
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
- The table shows the **documented** array (`PRESETS["documented"]`). `PRESETS["alternative"]` swaps the roles (omni at 1, 3, 5, 7), giving 4 omni / 3 bidirectional. See [`docs/STATUS.md`](docs/STATUS.md) for why both are included.
- The exact design does not depend on where the origin is. The Jacobi–Anger cross-check needs a centred array (see [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md#2-array-origin)).
- Look direction: θ = 0°, φ = 90° (end-fire). Prescribed nulls: ±106° and ±153° in the horizontal plane.

Every convention behind these choices is listed with its source in [`docs/CONVENTIONS.md`](docs/CONVENTIONS.md).

---

## What the code does

```
1. Geometry     src/lsa/array.py          →  microphone positions, types, and p_m (table above)
2. Steering     src/lsa/steering.py       →  3D steering vectors with one stated phase-sign convention
3. Design       src/lsa/beamformers.py    →  weights h(ω): exact null-constrained minimum-norm (headline)
                                              and Jacobi–Anger series expansion (cross-check)
4. Metrics      src/lsa/metrics.py        →  3D spherical-average DF and literal-Eq.-7 WNG
5. Comparison   src/lsa/reference.py      →  results checked against stored expected values and, once
                                              populated, the digitized reference curves in data/
```

`scripts/reproduce_all.py` runs all five stages. `scripts/make_figures.py` saves a polar beampattern and WNG/DF-versus-frequency plots to `figures/`. The original PyTorch script is kept untouched in [`legacy/`](legacy/README.md).

---

## Status

**Verified:** the beamformer satisfies the distortionless constraint and places its nulls at the prescribed angles, and this NumPy port reproduces the original script's results to within 0.005 dB. The original authors confirmed the 3 omni / 4 bidirectional configuration.

**Open:** for that documented array the White Noise Gain is roughly 8 dB below the published curve, while the 4 omni / 3 bidirectional array (the one the original script, as shipped, actually uses) lands within about 0.6 dB. The published paper reads this as a configuration inconsistency, but the authors' confirmation is in tension with that reading, so the cause is unresolved.

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
