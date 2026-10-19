# Pitfalls: symptom → cause → fix

These are the problems that cost the most time while reverse-engineering this beamformer. Each entry gives the symptom you will see, the cause, and how to fix or check it. Numbers were measured with the code in this repository (2026-10-19; c = 340 m/s, documented array unless stated).

| # | Symptom | Likely cause |
|---|---|---|
| [1](#1) | Distortionless error ≈ 1 and DF ≈ −21 dB | Steering sign differs between design and evaluation |
| [2](#2) | Distortionless error is 10⁻⁴–10⁻² instead of 10⁻¹⁴ | Series truncation in the Jacobi–Anger design (expected) |
| [3](#3) | WNG is extremely low (−41.5 dB at 500 Hz), weight norm about 119 | Physics of a second-order pattern from a 3 cm array (expected) |
| [4](#4) | Exact and Jacobi–Anger designs give almost the same WNG | They solve the same 3×3 system (see the derivation) |
| [5](#5) | Jacobi–Anger results change when the array is moved | The series is anchored at the origin: centre the array |
| [6](#6) | DF does not match figures in the 2023 letter | The letter's DF is a 2D average; this repo's is 3D |
| [7](#7) | `THE_LSA.py` gives the "wrong" array | Its comment says 3 omni + 4 bidirectional, but `pm` sets 4 omni + 3 bidirectional |
| [8](#8) | "Odd-indexed omni" gives a different array than expected | One-based vs zero-based indexing changes the sensor count |
| [9](#9) | Small gaps (0.1–0.6 dB) against the expected table | Speed of sound, WNG formula, grid, or design method |
| [10](#10) | WNG is 7–9 dB below the published curve | **Unresolved**, see [STATUS.md](STATUS.md) |

---

<a id="1"></a>
## 1. Distortionless error ≈ 1 and DF ≈ −21 dB

**Symptom.** `|dᴴ(θs)h − 1|` is about 0.97 (0.969 at 500 Hz) to 1.0 (1.013 at 3500 Hz). DF comes out near −21 dB instead of about +8.2 dB. WNG computed as `1/(hᴴh)` still looks correct (−41.5 dB at 500 Hz), and the literal WNG collapses to −71.2 dB, which also looks like "just a low WNG" if you are not looking for it.

**Cause.** The weights were designed with one steering-phase sign and evaluated with the opposite one. The 2023 letter uses `e^{+jωx cosθ}`; the EUSIPCO paper and the original script use `e^{−jωx cosθ sinφ / c}`. Each is self-consistent, but mixing them breaks the constraint.

**Why it is easy to miss.** WNG in its `1/(hᴴh)` form depends only on ‖h‖, so it is blind to this bug. A plausible WNG curve proves nothing about the design.

**Fix.** Use a single sign constant for design and evaluation (`PHASE_SIGN` in `src/lsa/steering.py`).

**Check.** Flip the sign in *both* places. DF and WNG must not change. Always print `|dᴴ(θs)h − 1|` before looking at any other metric. `tests/test_verification.py::test_wrong_phase_sign_breaks_distortionless_response` demonstrates the failure.

---

<a id="2"></a>
## 2. Distortionless error is 10⁻⁴–10⁻² instead of 10⁻¹⁴

**Symptom.** With the Jacobi–Anger design the look-direction error is 2×10⁻⁴ at 500 Hz and grows to 1×10⁻² at 3500 Hz.

**Cause.** Not a bug. The design truncates the Bessel series at order N = 2, so the constraint is met only approximately, and the error grows with frequency. The exact null-constrained design meets it to about 10⁻¹⁴.

**Fix.** Nothing. In tests, use separate tolerances: below 10⁻¹⁰ for the exact design, below 2×10⁻² for Jacobi–Anger.

---

<a id="3"></a>
## 3. WNG is extremely low and the weight norm is huge

**Symptom.** WNG is −41.5 dB at 500 Hz and ‖h‖ is about 119. It improves by about 12 dB per octave: −41.5 dB (500 Hz) → −29.5 dB (1 kHz) → −8.4 dB (3.5 kHz).

**Cause.** Not a bug. Building a second-order pattern with nulls from microphones spaced 0.5–1 cm apart requires large, opposing weights at low frequency. This is the known robustness cost of compact differential arrays.

**Fix.** Nothing to fix. Do not "improve" it by changing conventions. Check against `data/expected_results.csv` instead.

---

<a id="4"></a>
## 4. Exact and Jacobi–Anger designs give almost the same WNG

**Symptom.** You expected the least-squares Jacobi–Anger fit to relax the nulls and reduce the weight norm, raising WNG. It does not: the two designs differ by at most 0.18 dB in WNG and 0.065 dB in DF across 500–3500 Hz (the difference grows with frequency; below 1.5 kHz it is under 0.03 dB).

**Cause.** At end-fire, with `α = 90°`, the problem decouples and has no slack. At φ = 90° the response is

```
B(θ) = O(cos θ) + sin θ · P(cos θ)
```

where `O` collects the omnidirectional microphones and `P` the bidirectional ones. Each depends on θ only through cos θ.

1. **Look constraint.** At θs = 0, `sin θ = 0`, so `B(0) = O(1) = 1`. The bidirectional microphones do not enter.
2. **Null pairs.** Nulls sit at ±θn. At +θn, `O + sin θn · P = 0`. At −θn, `O − sin θn · P = 0`. Together these force `O(cos θn) = 0` **and** `P(cos θn) = 0`.
3. **Counting.** The three omnidirectional weights face three independent equations (look, 106°, 153°) for three unknowns, so the solution is unique. The bidirectional weights face only homogeneous constraints, so the minimum-norm solution sets them to **zero**.

So both designs solve essentially the same 3×3 system. Jacobi–Anger differs only by truncating the Bessel series at order 2, which is where the small difference comes from.

**Measured.**

| Check | Result |
|---|---|
| ‖h_bidirectional‖ of the exact solution, 500–3500 Hz | below 10⁻¹¹ (zero) |
| Omni-only 3×3 solve vs full exact design (WNG) | agree to 10⁻¹³ dB |
| Exact vs Jacobi–Anger, WNG | at most 0.18 dB apart |
| Exact vs Jacobi–Anger, DF | at most 0.065 dB apart |

**Consequence.** At end-fire the result depends only on the three omnidirectional microphones (1 cm apart), the target pattern, and `c`. A design with real slack needs more omnidirectional microphones: the 2023 letter reports that WNG improves substantially as sensors are added while DF stays almost constant.

---

<a id="5"></a>
## 5. Jacobi–Anger results change when the array is moved

**Symptom.** Shifting all microphones by +1.5 cm changes the Jacobi–Anger result: at 3500 Hz, DF goes from 8.066 to 8.463 dB and WNG from −8.563 to −9.985 dB. The exact design does not change.

**Cause.** The series expansion is anchored at the origin, and the letter specifies that the array centre is the origin.

**Fix.** Centre the array (`array.centered()`). `lsa.jacobi_anger` raises `ValueError` for an uncentred array rather than returning a quietly different answer.

---

<a id="6"></a>
## 6. DF does not match the 2023 letter's figures

**Cause.** The letter defines DF as an *azimuthal* (2D) average over θ. This repository follows the paper and averages over the *full sphere* (θ and φ). They are different quantities.

**Fix.** Compare like with like. Do not use DF values from the letter to check this code.

---

<a id="7"></a>
## 7. `THE_LSA.py` runs the "wrong" array

**Symptom.** You run `legacy/THE_LSA.py` as shipped and the WNG is far better (about 8 dB at 500 Hz) than what the documented 3 omni / 4 bidirectional array gives.

**Cause.** The script's comment reads "Example arrangement: 3 omni + 4 bidirectional", but the line below it sets `pm = [1, 0, 1, 0, 1, 0, 1]`, which is **four omni + three bidirectional** (`PRESETS["alternative"]`). To get the documented array, set `pm = [0, 1, 0, 1, 0, 1, 0]`.

**Fix.** Trust the numbers, not the comment. `python scripts/reproduce_all.py` prints the array table with counts for each preset. The script also imports PyTorch, but nothing it computes needs it; `src/lsa/` is the NumPy equivalent and reproduces the script's results (checked in `tests/`).

---

<a id="8"></a>
## 8. "Odd-indexed omni" produces the wrong array

**Cause.** In a 7-element array, one-based odd positions `{1, 3, 5, 7}` are four elements; zero-based odd indices `{1, 3, 5}` are three. They are complementary, so "omnidirectional at odd positions" gives either four omni + three bidirectional or three omni + four bidirectional depending on the convention.

**Fix.** Specify counts, not parity. The documented array is **3 omni + 4 bidirectional**, with bidirectional microphones at one-based positions 1, 3, 5, 7.

---

<a id="9"></a>
## 9. Small gaps (0.1–0.6 dB) against the expected table

**Cause.** These are the knobs that move results by a little, none of which can explain a large gap:

| Knob | Effect |
|---|---|
| Speed of sound (340 vs 343 vs 346 m/s) | ±0.15 dB WNG at 343; 0.45 dB at 331 m/s |
| WNG formula `1/(hᴴh)` vs `\|hᴴd\|²/(hᴴh)` | at most 0.09 dB (Jacobi–Anger only) |
| Exact vs Jacobi–Anger design | at most 0.18 dB WNG |
| DF integration grid | at most 0.00022 dB (original 72 × 36 grid) |

**Fix.** Match the conventions in [CONVENTIONS.md](CONVENTIONS.md) first.

---

<a id="10"></a>
## 10. WNG is 7–9 dB below the published curve

**Symptom.** Everything above checks out, DF matches the published curve closely, but WNG for the conventional LSA at θs = 0° sits roughly 7–9 dB below the digitized published curve for the documented 3 omni / 4 bidirectional array.

**Cause.** **Unresolved.** None of the items in this file explains it. Before assuming a new cause, confirm you are reading the correct curve: the figure has eight curves, and the conventional LSA at 0° is the least robust one. In this project the curve was confirmed with the original authors, so the gap remains.

**Also tested and ruled out: diagonal loading.** The original script contains a commented-out `h = Dᴴ(DDᴴ + λI)⁻¹ c`. On the documented array it does not help: λ = 10⁻⁶ moves the 500 Hz WNG from −41.5 to −40.7 dB and changes nothing above 2 kHz; larger λ degrades DF and fills the nulls (λ = 10⁻⁴: DF 5.8 dB and nulls only −14 / −17 dB at 500 Hz).

**What to do.** See [STATUS.md](STATUS.md) for what has been ruled out and what would settle it.
