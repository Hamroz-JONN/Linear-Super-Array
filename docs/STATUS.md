# Status

*Last updated: 2026-10-19*

This file states plainly what this repository has verified, what is still unresolved, and where the interpretation in the published paper is now in doubt.

## At a glance

| Item | State | Evidence |
|---|---|---|
| Distortionless steering constraint | ✅ Verified | Error about 10⁻¹⁴ (exact design); 2×10⁻⁴ to 1×10⁻² (Jacobi–Anger, series truncation) |
| Prescribed nulls at ±106°, ±153° | ✅ Verified | Exact design: response below 10⁻¹⁰ at all four null angles, 500–3500 Hz (checked by `reproduce_all.py` and the tests) |
| NumPy port reproduces the original script | ✅ Verified | Alternative array: within 0.0044 dB WNG and 0.0003 dB DF of the values reported in [Paper] (Eq. 39, 41), which came from `legacy/THE_LSA.py` |
| Two independent designs agree | ✅ Verified | WNG within 0.18 dB, DF within 0.065 dB, 500–3500 Hz (documented array) |
| Directivity Factor vs published curve | ✅ Matches closely | Mean absolute error 0.12 dB (documented) and 0.02 dB (alternative), as reported in [Paper]. The digitized values themselves are not yet in this repository |
| Array is 3 omnidirectional + 4 bidirectional | ✅ Confirmed by the original authors | Personal communication, [DATE] |
| Reference curve is the conventional LSA at θs = 0° | ✅ Confirmed by the original authors | Personal communication, [DATE] |
| White Noise Gain vs published curve, documented array | ❌ **Open** | Roughly 7–9 dB below the digitized curve; mean absolute error 8.07 dB as reported in [Paper] |
| White Noise Gain vs published curve, alternative array | ⚠️ Close, but inconsistent with the stated configuration | Mean absolute error 0.64 dB as reported in [Paper]; this is the 4 omni / 3 bidirectional array |
| Published paper's odd-indexed-omni explanation | ⚠️ **In tension with the authors' confirmation** | See the note below |

---

## Verified

- **Constraints and nulls.** The beamformer meets the look-direction constraint and places its nulls where prescribed. `python scripts/reproduce_all.py` and `pytest` check this on every run.
- **The port.** `src/lsa/` is a NumPy rewrite of the original PyTorch script. It reproduces the original script's reported alternative-array WNG and DF to the printed precision, so differences between this repository and the paper's numbers are not porting errors.
- **DF.** The reproduced Directivity Factor follows the published curve's level and trend. EUSIPCO does not tabulate numbers, so the comparison is against values digitized from the figure (uncertainty about 0.01 dB). Those values are not stored here yet; see `data/README.md`.
- **Configuration.** A co-author of the original paper confirmed the array has three omnidirectional and four bidirectional microphones, and that the curve used as reference is the conventional LSA at θs = 0°. The *positions* (bidirectional at the odd positions) are derived from the paper's orientation vector rather than separately confirmed.
- **Self-consistency.** Two different design methods (exact null-constrained and Jacobi–Anger) agree with each other, and swapping the phase-sign convention changes nothing when design and evaluation agree. See [PITFALLS.md](PITFALLS.md).

---

## Open: the White Noise Gain gap

For the documented array at end-fire (θs = 0°), the WNG produced by this repository is roughly 7–9 dB below the digitized published curve across 500–3500 Hz (mean absolute error 8.07 dB; for example −41.5 dB here against about −33 dB published at 500 Hz). The cause is **unresolved**.

**What this narrows down.** With α = 90°, the bidirectional microphones carry zero weight at end-fire ([PITFALLS.md §4](PITFALLS.md#4)). The WNG here is therefore fully determined by three quantities: the three omnidirectional microphones at 1 cm spacing, the target pattern (second-order supercardioid with nulls at ±106° and ±153°), and the speed of sound. For the published curve to differ, one of these must differ in the authors' implementation, or the published curve comes from a different problem formulation than the one documented.

**A finding about the original script.** `legacy/THE_LSA.py`, as shipped, sets `pm = [1, 0, 1, 0, 1, 0, 1]`: four omnidirectional and three bidirectional microphones, although the comment on that line says "3 omni + 4 bidirectional". The documented-array results therefore require editing `pm`. The structure of the 2023 letter's own array (M omni + (M−1) bidirectional, omni at both ends) is also four omni + three bidirectional for M = 4. Neither fact shows which array produced the published curve, but both are consistent with it being the 4 / 3 one.

**Not yet tested.**

- The implementation details in the 2024 IEEE/ACM TASLP paper that a co-author recommended for this baseline ("Design of Fully Steerable Differential Beamformers With Linear Superarrays"). The numbers in this repository follow the 2023 letter and the EUSIPCO paper only.
- The authors' own code.

### Ruled out, with measured effect

| Candidate cause | Measured effect |
|---|---|
| Phase-sign convention | None if consistent |
| Speed of sound | ±0.15 dB per ±3 m/s; an 8 dB shift would need c ≈ 214 m/s |
| DF integration grid | At most 0.00022 dB (original 72 × 36 grid) |
| WNG formula variant | At most 0.09 dB |
| Design method (exact vs Jacobi–Anger) | At most 0.18 dB |
| Array origin | None (exact design); at most 1.4 dB at 3.5 kHz (Jacobi–Anger only) |
| Diagonal loading (the original script's commented-out solver) | λ = 10⁻⁶: 0.8 dB at 500 Hz, nothing above 2 kHz. Larger λ ruins DF and the nulls |
| float32 vs float64 | No visible effect |
| Reading the wrong curve in the figure | Confirmed correct by the original authors |
| Digitization error | About 0.016 dB for WNG, against an 8 dB gap |
| Microphone counts | Confirmed by the original authors |

---

## A note on the published paper

The published paper ([doi:10.65161/recC6aX4oKVBJEXdP](https://doi.org/10.65161/recC6aX4oKVBJEXdP)) reports that assigning omnidirectional microphones to the odd-indexed positions (one-based), which gives **four omnidirectional and three bidirectional** microphones, reproduces the digitized published curves: WNG error falls from 8.07 dB to 0.64 dB, and DF error from 0.12 dB to 0.02 dB. It interprets this as evidence of an inconsistency between the documented microphone configuration and the configuration used to generate the published curves.

**The authors of the original paper subsequently confirmed that their array has three omnidirectional and four bidirectional microphones.** That is in tension with the paper's interpretation, and the interpretation should not be relied on as established. What the evidence supports is narrower: a four-omni array lands close to the published WNG curve, and the documented three-omni array does not, under every convention tested here. It does not identify which array, or which formulation, produced the published curve.

<!-- TODO: if an erratum or addendum is filed with the journal, link it here. -->

---

## What would settle it

1. The authors' code, or confirmation of which array and which formulation generated the published WNG curve (in particular, whether it used the 2023 letter's M omni + (M−1) bidirectional structure).
2. An implementation following the 2024 TASLP paper.
3. Any independent implementation that reproduces the published end-fire WNG for the documented array. If you have one, please open an issue.

---

## Run the verification yourself

```bash
python scripts/reproduce_all.py   # prints the DF / WNG tables and runs the checks
pytest -q                         # distortionless error, nulls, geometry, DF sanity, regression
```

<!-- TODO before publishing: fill [DATE] (twice). Ask the authors' permission to cite the correspondence as "personal communication". -->
