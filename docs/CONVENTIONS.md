# Conventions and judgment calls

Neither the EUSIPCO paper nor the 2023 letter specifies everything needed to run this beamformer. This file records every choice made in this repository, where it came from, and what changes if you choose differently. All effects were measured with the code in this repository (`src/lsa/`, run 2026-10-19).

**Sources**

| Tag | Reference |
|---|---|
| **[EUSIPCO]** | W. Huang and E. A. P. Habets, "Robust differential beamformers for linear superarrays with non-uniformly oriented directional microphones," *Proc. EUSIPCO*, 2025. The paper being reproduced. |
| **[Letter]** | X. Luo, J. Jin, G. Huang, J. Chen, J. Benesty, "Design of Steerable Linear Differential Microphone Arrays With Omnidirectional and Bidirectional Sensors," *IEEE Signal Processing Letters* 30, 463–467, 2023. [doi:10.1109/LSP.2023.3267969](https://doi.org/10.1109/LSP.2023.3267969). Source of the Jacobi–Anger design method. |
| **[Paper]** | The published reproduction study for this repository ([doi:10.65161/recC6aX4oKVBJEXdP](https://doi.org/10.65161/recC6aX4oKVBJEXdP)), which defines the evaluation (3D Directivity Factor, White Noise Gain). |
| **[Script]** | `legacy/THE_LSA.py`, the original PyTorch script that produced the results in [Paper]. |

**Status labels**

- **Stated**: given in a source above.
- **Confirmed**: confirmed by the original authors in personal communication.
- **Derived**: follows from stated facts; not directly confirmed.
- **Chosen**: not specified by any source I had access to. My choice, with its measured effect.

---

## Summary

| # | Convention | Choice in this repo | Status | Effect if changed |
|---|---|---|---|---|
| 1 | [Layout and indexing](#1-array-layout-and-indexing) | One-based. Documented array: bidirectional at 1, 3, 5, 7; omni at 2, 4, 6 | Counts **confirmed**; positions **derived** | A different array (the "alternative" preset) |
| 2 | [Array origin](#2-array-origin) | Exact design: positions 0 to 3 cm. Jacobi–Anger: centred | **Stated** [Letter] | Exact design: none. Jacobi–Anger: up to 1.4 dB WNG at 3.5 kHz |
| 3 | [Phase sign](#3-phase-sign-convention) | `−j`: `e^{−jωx cosθ sinφ / c}`, rows `dᴴ` | **Stated** [EUSIPCO], [Script] | None if design and evaluation agree. DF collapses to about −21 dB if mixed |
| 4 | [Speed of sound](#4-speed-of-sound) | 340 m/s | **Stated** by [Script] | About ±0.15 dB WNG per ±3 m/s. DF unchanged |
| 5 | [Directional response](#5-directional-response-and-orientation) | `g = p + (1−p)·cos(θ−α)·sin φ`, α = 90° | **Stated** [EUSIPCO], [Script] | At α = 90° the bidirectional mics are silent at end-fire |
| 6 | [Design vs evaluation](#6-design-plane-target-pattern-and-evaluation) | Designed in the horizontal plane. DF averaged over the full sphere | **Stated** | 2D and 3D DF are different quantities |
| 7 | [Target pattern](#6-design-plane-target-pattern-and-evaluation) | 2nd-order supercardioid, nulls at ±106° and ±153° | **Stated** [Letter], [EUSIPCO] | Defines the design |
| 8 | [Solver](#7-solver) | Exact: `pinv(D, rcond=1e-12)`, no regularization | **Stated** by [Script] | Diagonal loading does not close the WNG gap |
| 9 | [DF quadrature](#8-df-integration-grid) | Gauss–Legendre, 360 × 100 | **Chosen** | Original 72 × 36 grid: at most 0.00022 dB |
| 10 | [WNG formula](#9-wng-definition) | `\|dᴴh\|²/(hᴴh)` in dB | **Stated** [EUSIPCO] Eq. 7 | At most 0.09 dB (Jacobi–Anger) |
| 11 | [Reference curve](#10-reference-data) | Conventional LSA at θs = 0° | **Confirmed** | The figure holds eight curves |

---

## 1. Array layout and indexing

**Choice.** One-based indices `m = 1…7`; microphone `m` sits at `x = (m − 1) × 0.5 cm`. The **documented** array has bidirectional microphones at `m = 1, 3, 5, 7` and omnidirectional at `m = 2, 4, 6`. Adjacent spacing 0.5 cm, aperture 3 cm.

**Source.**

- Three omni + four bidirectional at 0.5 cm spacing is stated in [EUSIPCO]. The counts were **confirmed** by a co-author of [EUSIPCO] (personal communication, [DATE]).
- Positions are **derived**. The orientation vector in [EUSIPCO] has the form `[α₁, 0, α₃, 0, π−α₃, 0, π−α₁]`, which puts the four directional microphones at the odd positions. Given the confirmed counts and strict alternation, this is the only layout that fits. The co-author's confirmation covered the counts, not the positions.
- [Letter] writes its positions for M omni + (M−1) bidirectional, with omni at both ends. For M = 4 that is **four omni + three bidirectional**, the opposite majority from the documented array.

**The alternative preset.** `PRESETS["alternative"]` has omnidirectional microphones at `m = 1, 3, 5, 7` (four omni, three bidirectional). It is *not* the configuration the authors confirmed, but it is the one that reproduces the published curves (see [STATUS.md](STATUS.md)), and it is the one that `legacy/THE_LSA.py` sets as shipped (`pm = [1,0,1,0,1,0,1]`, despite its comment saying "3 omni + 4 bidirectional").

**Why it matters.** "Odd-indexed" is ambiguous. In a 7-element array, the one-based odd positions `{1, 3, 5, 7}` are four elements, while the zero-based odd indices `{1, 3, 5}` are three. They are complementary sets. State counts, not parity.

---

## 2. Array origin

**Choice.** The exact design uses positions 0 to 3 cm, as [Script] does. The exact design is **origin-invariant**: a shift multiplies each steering vector by a unit-modulus phase and leaves |B| and ‖h‖ unchanged (tested). The Jacobi–Anger cross-check requires a centred array (`x = (m − 4) × 0.5 cm`, −1.5 to +1.5 cm) and the code raises `ValueError` otherwise; use `array.centered()`.

**Source.** **Stated** in [Letter] §II: "The center of the array is chosen as the origin of the coordinate system."

**Why it matters.** The Jacobi–Anger series is expanded about the origin, so shifting the array changes the weights it produces.

| Design | f (Hz) | DF / WNG (dB) |
|---|---|---|
| Jacobi–Anger, centred | 500 | 8.210 / −41.513 |
| Jacobi–Anger, shifted by +1.5 cm | 500 | 8.218 / −41.558 |
| Jacobi–Anger, centred | 3500 | 8.066 / −8.563 |
| Jacobi–Anger, shifted by +1.5 cm | 3500 | 8.463 / −9.985 |
| Exact (any position) | 500 | 8.211 / −41.520 |
| Exact (any position) | 3500 | 8.001 / −8.384 |

---

## 3. Phase sign convention

**Choice.** `d_m = g_m · e^{−jωx_m cosθ sinφ / c}`, constraint rows `dᴴ`, beampattern `B = dᴴh`. The constant `PHASE_SIGN = −1` lives in `src/lsa/steering.py` and is used by design and evaluation alike.

**Source.** **Stated** in [EUSIPCO] (Eq. 3 and 5) and used by [Script]. [Letter] uses `+j`. The two are complex conjugates.

**Why it matters.** DF and WNG are identical provided design and evaluation use the *same* sign. Mixing them breaks the distortionless constraint. Measured on the exact design for the documented array, designed with `+j` and evaluated with `−j`:

| f (Hz) | `\|B(θs) − 1\|` | DF (dB) | WNG literal (dB) | WNG as `1/(hᴴh)` (dB) |
|---|---|---|---|---|
| 500 | **0.969** | **−21.5** | −71.2 | −41.5 |
| 3500 | **1.013** | **−21.0** | −37.4 | −8.4 |

The simplified `1/(hᴴh)` form is blind to this bug, which is one reason the repository uses the literal form. Always check the distortionless error first. See [PITFALLS.md](PITFALLS.md#1).

**If you use the Letter's `+j`:** the Jacobi–Anger matrix entries change from `(+j)ⁿ Jₙ(ωx/c)` to `(−j)ⁿ Jₙ(ωx/c)`, from `e^{jμ cosθ} = Σ jⁿ Jₙ(μ) e^{jnθ}` ([Letter] Eq. 37). In this repository both follow `PHASE_SIGN`. Flip design and evaluation together.

---

## 4. Speed of sound

**Choice.** `c = 340 m/s`.

**Source.** [Script] sets `c0 = 340.0`, and the results in [Paper] were generated with it. [EUSIPCO] and [Letter] say only "the speed of sound in air" as far as I could check.

**Why it matters.** The array enters only through `ωx/c`, so changing `c` by a factor `k` is equivalent to rescaling every frequency by `1/k`. Documented array, exact design, WNG at 500 Hz:

| c (m/s) | Context | WNG (dB) | Δ vs 340 m/s |
|---|---|---|---|
| 331.3 | 0 °C | −41.070 | +0.45 dB |
| **340.0** | **repo default** | **−41.520** | **0** |
| 343.0 | ~20 °C | −41.672 | −0.15 dB |
| 346.1 | 25 °C | −41.828 | −0.31 dB |

DF changes by less than 0.001 dB across this range. A shift of 8 dB at 500 Hz would need `c ≈ 214 m/s`, which is not a physical value for air.

---

## 5. Directional response and orientation

**Choice.** Each microphone has response

```
g_m(θ, φ) = p_m + (1 − p_m) · cos(θ − α_m) · sin φ
```

with `p_m = 1` omnidirectional and `p_m = 0` a pure dipole. All bidirectional microphones use `α_m = π/2` (90°).

**Source.** The response model is **stated** in [EUSIPCO] (Eq. 5, as cited in [Script]). `α = π/2` for all directional microphones in the conventional LSA is **stated** in [EUSIPCO], which describes them as oriented toward broadside, and [Script] uses it.

**Why it matters.** With `α = π/2`, `cos(θ − π/2) = sin θ`, so `g = sin θ · sin φ`, which is **zero at the look direction** θ = 0. At end-fire the bidirectional microphones therefore contribute nothing to the look-direction constraint and (shown in [PITFALLS.md](PITFALLS.md#4)) the minimum-norm solution gives them exactly zero weight. If α were anything other than π/2, this would change.

---

## 6. Design plane, target pattern, and evaluation

**Target pattern.** A 2nd-order supercardioid, `B(θ) = Σₙ αₙ cos(n(θ − θs))`, with `(α₀, α₁, α₂) = (0.309, 0.484, 0.207)`, which sum to 1. Look direction `θs = 0°`, `φs = 90°`. Nulls at `θs ± 106°` and `θs ± 153°`.

**Source.** **Stated.** The coefficients and null angles appear in [Letter] §V (nulls listed at θs + 106° and θs + 153°), and [EUSIPCO] lists nulls at θs ± 106° and θs ± 153°. At θs = 0 the pattern is mirror-symmetric, so the "+" nulls imply the "−" nulls.

**Design is two-dimensional; evaluation is three-dimensional.**

- Both designs constrain the horizontal plane only (φ = 90°). The weights never see other elevations.
- DF is evaluated over the **full sphere**, as in [Paper]. The [Letter]'s own DF is an *azimuthal* average, so DF values from the [Letter]'s figures are not comparable with the DF reported here.

**Orders.** For order N = 2, [Letter] requires at least N + 1 = 3 omnidirectional and N = 2 bidirectional sensors. The documented array has 3 and 4. At θs = 0 the bidirectional target coefficients vanish, because they are proportional to sin(nθs).

---

## 7. Solver

**Choice.** `h = pinv(D, rcond=1e-12) · [1, 0, 0, 0, 0]ᵀ`, where the rows of `D` are `d(θᵢ)ᴴ` for θᵢ ∈ {0°, ±106°, ±153°}. No regularization.

**Source.** **Stated** by [Script], whose active solver is this one. It also contains a commented-out diagonal-loading alternative (`h = Dᴴ(DDᴴ + λI)⁻¹ c`, λ = 10⁻⁶).

**Why it matters.** Diagonal loading was tested as a possible explanation for the open WNG gap and does not explain it: at λ = 10⁻⁶ the 500 Hz WNG moves from −41.5 to −40.7 dB and nothing changes above 2 kHz, while larger λ fills the nulls (at λ = 10⁻⁴ and 500 Hz the nulls are only −14 and −17 dB deep and DF falls to 5.8 dB). See [PITFALLS.md](PITFALLS.md#10).

---

## 8. DF integration grid

**Choice.** The spherical average uses uniform azimuth and Gauss–Legendre nodes in `cos φ` (default 360 × 100), with weights summing to 1. `legacy_grid()` reproduces [Script]'s 72 × 36 grid (uniform azimuth, trapezoid rule in φ, poles included).

**Source.** The default is **chosen**. [Script] uses the 72 × 36 grid.

**Convergence.** Documented array, exact design, against a 720 × 200 Gauss–Legendre reference (DF = 8.210549 dB at 500 Hz, 8.001187 dB at 3500 Hz):

| Grid | Error at 500 Hz (dB) | Error at 3500 Hz (dB) |
|---|---|---|
| **360 × 100 (repo default)** | below 10⁻¹² | below 10⁻¹² |
| 90 × 25 Gauss–Legendre | below 10⁻¹² | below 10⁻¹² |
| 72 × 36 trapezoid ([Script]) | +2.0×10⁻⁴ | +2.2×10⁻⁴ |

The grid is not a source of any visible discrepancy.

---

## 9. WNG definition

**Choice.** `WNG = |d(θs)ᴴh|² / (hᴴh)`, reported as `10·log₁₀(WNG)`. DF is likewise `10·log₁₀(DF)`.

**Source.** **Stated** in [EUSIPCO] Eq. 7 (as cited in [Script]: "Literal Eq. (7)"). [Paper] also uses the form `1/(hᴴh)`, which is equal under the distortionless constraint `dᴴh = 1`.

**Why it matters.** The exact design satisfies the constraint to about 10⁻¹⁴, so the two forms agree. The Jacobi–Anger design truncates its series at order 2, so its look-direction error is 2×10⁻⁴ at 500 Hz, growing to 1×10⁻² at 3500 Hz. The literal form is then lower than `1/(hᴴh)` by 0.002 dB at 500 Hz and 0.091 dB at 3500 Hz.

---

## 10. Reference data

**Choice.** The published WNG and DF values come from the curve for the **conventional LSA at θs = 0°** (end-fire).

**Source.** **Confirmed.** The WNG figure in [EUSIPCO] shows eight curves: LSA and LSA+ at steering angles 0°, 30°, 60°, and 90°. A co-author of [EUSIPCO] confirmed that the curve being read is the conventional LSA at 0° (personal communication, [DATE]).

**Digitization.** [EUSIPCO] does not tabulate numerical values, so reference values must be read off the figure ([Paper] describes the procedure and estimates the uncertainty at 0.016 dB for WNG and 0.011 dB for DF). `data/reference_digitized.csv` is the place for those readings; it is an empty template until populated, and records the tool, version and date per row.

**Why it matters.** The conventional LSA at 0° is the *least* robust of the eight curves. A reproduction that lands far above or below it should first check that it is comparing against the right line.

---

## Not specified by any source I had access to

- Whether the authors' implementation adds regularization. [Letter] does not mention it. A diagonal-loading test did not close the gap ([§7](#7-solver)).
- The implementation details in the 2024 IEEE/ACM TASLP paper recommended by a co-author. Numbers here follow the 2023 letter, [EUSIPCO] and [Script] only.

<!-- TODO before publishing: fill [DATE] (twice, for the correspondence). Ask the authors' permission to cite the correspondence as "personal communication". -->
