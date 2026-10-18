# Status

*Last updated: 2026-10-18*

This file states plainly what this repository has verified, what is still unresolved, and a correction to the interpretation in the published paper.

## At a glance

| Item | State | Evidence |
|---|---|---|
| Distortionless steering constraint | ✅ Verified | Error about 10⁻¹⁵ (exact design); 2×10⁻⁴ to 1×10⁻² (Jacobi–Anger, series truncation) |
| Prescribed nulls at ±106°, ±153° | ✅ Verified | Exact design: minima at ±106.1° and ±153.0° (−67 and −82 dB, grid-limited). Jacobi–Anger at 1 kHz: ±105.9° and ±153.2° |
| Directivity Factor vs published curve | ✅ Matches to about 0.1 dB | Mean absolute error 0.12 dB against values digitized from the figure |
| Array is 3 omnidirectional + 4 bidirectional | ✅ Confirmed by the original authors | Personal communication, [DATE] |
| Reference curve is the conventional LSA at θs = 0° | ✅ Confirmed by the original authors | Personal communication, [DATE] |
| Two independent designs agree | ✅ Verified | WNG within 0.09 dB, DF within 0.064 dB, 500–3500 Hz |
| White Noise Gain vs published curve | ❌ **Open** | Roughly 7–9 dB below the digitized curve; mean absolute error 8.07 dB |
| Published paper's odd-indexed-omni explanation | ⚠️ **Contradicted by the authors' confirmation** | See the note below |

---

## Verified

- **Constraints and nulls.** The beamformer meets the look-direction constraint and places its nulls where prescribed. Null *depths* in the figures are limited by the azimuth sampling grid, not by the design.
- **DF.** The reproduced Directivity Factor follows the published curve's level and trend. The published paper does not tabulate numbers, so the comparison is against values digitized from the figure (uncertainty about 0.01 dB), and the match is to about 0.1 dB.
- **Configuration.** A co-author of the original paper confirmed the array has three omnidirectional and four bidirectional microphones, and that the curve used as reference is the conventional LSA at θs = 0°. The *positions* (bidirectional at the odd positions) are derived from the paper's orientation vector rather than separately confirmed.
- **Self-consistency.** Two different design methods (exact null-constrained and Jacobi–Anger) agree with each other, and swapping the phase-sign convention changes nothing when design and evaluation agree. See [PITFALLS.md](PITFALLS.md).

---

## Open: the White Noise Gain gap

For the documented array at end-fire (θs = 0°), the WNG produced by this repository is roughly 7–9 dB below the digitized published curve across 500–3500 Hz (mean absolute error 8.07 dB; for example −41.7 dB here against about −32 dB published at 500 Hz). The cause is **unresolved**.

**What this narrows down.** With α = 90°, the bidirectional microphones carry zero weight at end-fire ([PITFALLS.md §4](PITFALLS.md#4)). The WNG here is therefore fully determined by three quantities: the three omnidirectional microphones at 1 cm spacing, the target pattern (second-order supercardioid with nulls at ±106° and ±153°), and the speed of sound. For the published curve to differ, one of these must differ in the authors' implementation, or the published curve comes from a different problem formulation than the one documented.

**Not yet tested.**

- Regularization or a robustness constraint (for example, diagonal loading) in the authors' implementation.
- A different omnidirectional count or spacing than documented.
- The implementation details in the 2024 IEEE/ACM TASLP paper that a co-author recommended for this baseline ("Design of Fully Steerable Differential Beamformers With Linear Superarrays"). The numbers in this repository follow the 2023 letter and the EUSIPCO paper only.

### Ruled out, with measured effect

| Candidate cause | Measured effect |
|---|---|
| Phase-sign convention | None if consistent (identical to 3 decimals) |
| Speed of sound | ±0.15 dB per ±3 m/s; an 8 dB shift would need c ≈ 215 m/s |
| DF integration grid | Below 10⁻⁵ dB |
| WNG formula variant | At most 0.09 dB |
| Design method (exact vs Jacobi–Anger) | At most 0.09 dB |
| Array origin | None (exact design); at most 1.7 dB at 3.5 kHz and 0.05 dB at 500 Hz (Jacobi–Anger) |
| Reading the wrong curve in the figure | Confirmed correct by the original authors |
| Digitization error | About 0.016 dB for WNG, against an 8 dB gap |
| Microphone counts | Confirmed by the original authors |

---

## A note on the published paper

The published paper ([doi:10.65161/recC6aX4oKVBJEXdP](https://doi.org/10.65161/recC6aX4oKVBJEXdP)) reports that assigning omnidirectional microphones to the odd-indexed positions (one-based), which gives **four omnidirectional and three bidirectional** microphones, reproduces the digitized published curves: WNG error falls from 8.07 dB to 0.64 dB, and DF error from 0.12 dB to 0.02 dB. It interprets this as evidence of an inconsistency between the documented microphone configuration and the configuration used to generate the published curves.

**The authors of the original paper subsequently confirmed that their array has three omnidirectional and four bidirectional microphones.** The "alternative" assignment is therefore a different array from the one they used. This contradicts the paper's interpretation, and **that interpretation should not be relied on.**

What remains accurate: the implementation and verification described above, the DF agreement, and the numerical observation that a four-omni array lands close to the published WNG curve. That observation is consistent with the 2023 letter's finding that WNG improves as omnidirectional sensors are added, but it does not identify which array produced the published curve.

<!-- TODO: if an erratum or addendum is filed with the journal, link it here. -->

---

## What would settle it

1. The authors' code, or confirmation of whether their implementation uses regularization or a robustness constraint.
2. An implementation following the 2024 TASLP paper.
3. Any independent implementation that reproduces the published end-fire WNG. If you have one, please open an issue.

---

## Run the verification yourself

```bash
python scripts/reproduce_all.py   # prints the DF / WNG table
pytest tests/                     # distortionless error, null locations, geometry, DF sanity
```

<!-- TODO before publishing: fill [DATE] (twice). Ask the authors' permission to cite the correspondence as "personal communication". -->
