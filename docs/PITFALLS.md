# Pitfalls: symptom → cause → fix

These are the problems that cost the most time while reverse-engineering this beamformer. Each entry gives the symptom you will see, the cause, and how to fix or check it. Numbers were measured with the code in this repository (2026-10-18).

| # | Symptom | Likely cause |
|---|---|---|
| [1](#1) | Distortionless error ≈ 0.97 and DF ≈ −21 dB, but WNG looks fine | Steering sign differs between design and evaluation |
| [2](#2) | Distortionless error is 10⁻⁴–10⁻² instead of 10⁻¹⁵ | Series truncation in the Jacobi–Anger design (expected) |
| [3](#3) | WNG is extremely low (−42 dB at 500 Hz), weight norm about 120 | Physics of a second-order pattern from a 3 cm array (expected) |
| [4](#4) | Exact and Jacobi–Anger designs give almost the same WNG | They solve the same 3×3 system (see the derivation) |
| [5](#5) | Jacobi–Anger results change when the array is moved | The series is anchored at the origin: centre the array |
| [6](#6) | DF does not match figures in the 2023 letter | The letter's DF is a 2D average; this repo's is 3D |
| [7](#7) | Weights or positions do not line up with the array table | Vectors are ordered by type, not by array index |
| [8](#8) | "Odd-indexed omni" gives a different array than expected | One-based vs zero-based indexing changes the sensor count |
| [9](#9) | Small gaps (0.1–0.6 dB) against the expected table | Speed of sound, WNG formula, grid, or design method |
| [10](#10) | WNG is 7–9 dB below the published curve | **Unresolved**, see [STATUS.md](STATUS.md) |

---

<a id="1"></a>
## 1. Distortionless error ≈ 0.97 and DF ≈ −21 dB, but WNG looks fine

**Symptom.** `|h^H d(θs) − 1|` is about 0.97 (0.968 at 500 Hz, 0.961 at 3500 Hz). DF comes out near −21 dB (−21.6 dB at 500 Hz, −20.1 dB at 3500 Hz) instead of about +8.2 dB. WNG is the correct −41.663 dB (500 Hz) and −8.611 dB (3500 Hz).

**Cause.** The weights were designed with one steering-phase sign and evaluated with the opposite one. The 2023 letter uses `e^{+jωx cosθ}`; the paper's draft used `e^{−jωx cosθ sinφ / c}`. Each is self-consistent, but mixing them breaks the constraint.

**Why it is easy to miss.** WNG depends only on ‖h‖, so it is blind to this bug. A plausible WNG curve proves nothing about the design.

**Fix.** Use a single sign constant for design and evaluation. If you use the Jacobi–Anger design, the matrix rows `(−j)ⁿ Jₙ(ωx/c)` go with `+j`; with `−j` they become `(+j)ⁿ Jₙ(ωx/c)`.

**Check.** Flip the sign in *both* places. DF and WNG must not change (8.210 dB / −41.663 dB at 500 Hz either way). Always print `|h^H d(θs) − 1|` before looking at any other metric.

---

<a id="2"></a>
## 2. Distortionless error is 10⁻⁴–10⁻² instead of 10⁻¹⁵

**Symptom.** With the Jacobi–Anger design the look-direction error is 2×10⁻⁴ at 500 Hz and grows to 1×10⁻² at 3500 Hz.

**Cause.** Not a bug. The design truncates the Bessel series at order N = 2, so the constraint is met only approximately, and the error grows with frequency. The exact null-constrained design meets it to about 10⁻¹⁵.

**Fix.** Nothing. In tests, use separate tolerances: below 10⁻¹² for the exact design, below 2×10⁻² for Jacobi–Anger.

---

<a id="3"></a>
## 3. WNG is extremely low and the weight norm is huge

**Symptom.** WNG is −41.7 dB at 500 Hz and ‖h‖ is about 121. It improves by about 12 dB per octave: −41.7 dB (500 Hz) → −29.7 dB (1 kHz) → −8.6 dB (3.5 kHz).

**Cause.** Not a bug. Building a second-order pattern with nulls from microphones spaced 0.5–1 cm apart requires large, opposing weights at low frequency. This is the known robustness cost of compact differential arrays.

**Fix.** Nothing to fix. Do not "improve" it by changing conventions. Check against the expected table instead.

---

<a id="4"></a>
## 4. Exact and Jacobi–Anger designs give almost the same WNG

**Symptom.** You expected the least-squares Jacobi–Anger fit to relax the nulls and reduce the weight norm, raising WNG. It does not: the two designs differ by at most 0.09 dB in WNG and 0.064 dB in DF across 500–3500 Hz.

**Cause.** At end-fire, with `α = 90°`, the problem decouples and has no slack. At φ = 90° the response is

```
B(θ) = O(cos θ) + sin θ · P(cos θ)
```

where `O` collects the omnidirectional microphones and `P` the bidirectional ones. Each depends on θ only through cos θ.

1. **Look constraint.** At θs = 0, `sin θ = 0`, so `B(0) = O(1) = 1`. The bidirectional microphones do not enter.
2. **Null pairs.** Nulls sit at ±θn. At +θn, `O + sin θn · P = 0`. At −θn, `O − sin θn · P = 0`. Together these force `O(cos θn) = 0` **and** `P(cos θn) = 0`.
3. **Counting.** The three omnidirectional weights face three independent equations (look, 106°, 153°) for three unknowns, so the solution is unique. The bidirectional weights face only homogeneous constraints, so the minimum-norm solution sets them to **zero**.

So both designs solve the same 3×3 system. Jacobi–Anger differs only by truncating the Bessel series at order 2, which is where the sub-0.1 dB difference comes from.

**Measured.**

| Check | Result |
|---|---|
| ‖h_bidirectional‖ of the exact solution | below 6×10⁻¹² (zero) |
| Omni-only 3×3 solve vs full exact design (WNG) | agree to 10⁻¹³ dB |
| Exact vs Jacobi–Anger, WNG | at most 0.09 dB apart |
| Exact vs Jacobi–Anger, DF | at most 0.064 dB apart |

**Consequence.** At end-fire the result depends only on the three omnidirectional microphones (1 cm apart), the target pattern, and `c`. A design with real slack needs more omnidirectional microphones: the 2023 letter reports that WNG improves substantially as sensors are added while DF stays almost constant.

---

<a id="5"></a>
## 5. Jacobi–Anger results change when the array is moved

**Symptom.** Shifting all microphones by +1.5 cm changes the Jacobi–Anger result: at 3500 Hz, DF goes from 8.069 to 8.459 dB and WNG from −8.611 to −10.342 dB. The exact design does not change.

**Cause.** The series expansion is anchored at the origin, and the letter specifies that the array centre is the origin.

**Fix.** Centre the array: `x_m = (m − 4) × 0.5 cm`.

---

<a id="6"></a>
## 6. DF does not match the 2023 letter's figures

**Cause.** The letter defines DF as an *azimuthal* (2D) average over θ. This repository follows the paper and averages over the *full sphere* (θ and φ). They are different quantities.

**Fix.** Compare like with like. Do not use DF values from the letter to check this code.

---

<a id="7"></a>
## 7. Weights or positions do not line up with the array table

**Cause.** In the original single-file script, positions and weights are ordered by type: three omnidirectional entries first, then four bidirectional ones. The README table is ordered by array index.

**Fix.** Sort by position before comparing, or build vectors per index using the `p_m` table.

---

<a id="8"></a>
## 8. "Odd-indexed omni" produces the wrong array

**Cause.** In a 7-element array, one-based odd positions `{1, 3, 5, 7}` are four elements; zero-based odd indices `{1, 3, 5}` are three. They are complementary, so "omnidirectional at odd positions" gives either four omni + three bidirectional or three omni + four bidirectional depending on the convention.

**Fix.** Specify counts, not parity. This repository's array is **3 omni + 4 bidirectional**, with bidirectional microphones at one-based positions 1, 3, 5, 7.

---

<a id="9"></a>
## 9. Small gaps (0.1–0.6 dB) against the expected table

**Cause.** These are the knobs that move results by a little, none of which can explain a large gap:

| Knob | Effect |
|---|---|
| Speed of sound (340 vs 343 vs 346 m/s) | ±0.15 dB WNG; 0.6 dB at 331 m/s |
| WNG formula `1/(hᴴh)` vs `|hᴴd|²/(hᴴh)` | at most 0.09 dB (Jacobi–Anger only) |
| Exact vs Jacobi–Anger design | at most 0.09 dB WNG |
| DF integration grid | about 10⁻⁴ dB even at 91 × 46; below 10⁻⁵ dB at the repo's 361 × 181 |

**Fix.** Match the conventions in [CONVENTIONS.md](CONVENTIONS.md) first.

---

<a id="10"></a>
## 10. WNG is 7–9 dB below the published curve

**Symptom.** Everything above checks out, DF matches the published curve to about 0.1 dB, but WNG for the conventional LSA at θs = 0° sits roughly 7–9 dB below the digitized published curve.

**Cause.** **Unresolved.** None of the items in this file explains it. Before assuming a new cause, confirm you are reading the correct curve: the figure has eight curves, and the conventional LSA at 0° is the least robust one. In this project the curve was confirmed with the original authors, so the gap remains.

**What to do.** See [STATUS.md](STATUS.md) for what has been ruled out and what would settle it.
