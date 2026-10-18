# Conventions and judgment calls

Neither the EUSIPCO paper nor the 2023 letter specifies everything needed to run this beamformer. This file records every choice made in this repository, where it came from, and what changes if you choose differently. All effects were measured with the code in this repository (checks run 2026-10-18).

**Sources**

| Tag | Reference |
|---|---|
| **[EUSIPCO]** | W. Huang and E. A. P. Habets, "Robust differential beamformers for linear superarrays with non-uniformly oriented directional microphones," *Proc. EUSIPCO*, 2025. The paper being reproduced. |
| **[Letter]** | X. Luo, J. Jin, G. Huang, J. Chen, J. Benesty, "Design of Steerable Linear Differential Microphone Arrays With Omnidirectional and Bidirectional Sensors," *IEEE Signal Processing Letters* 30, 463–467, 2023. [doi:10.1109/LSP.2023.3267969](https://doi.org/10.1109/LSP.2023.3267969). Source of the Jacobi–Anger design method. |
| **[Paper]** | The published reproduction study for this repository ([doi:10.65161/recC6aX4oKVBJEXdP](https://doi.org/10.65161/recC6aX4oKVBJEXdP)), which defines the evaluation (3D Directivity Factor, White Noise Gain). |

**Status labels**

- **Stated**: given in a source above.
- **Confirmed**: confirmed by the original authors in personal communication.
- **Derived**: follows from stated facts; not directly confirmed.
- **Chosen**: not specified by any source I had access to. My choice, with its measured effect.

---

## Summary

| # | Convention | Choice in this repo | Status | Effect if changed |
|---|---|---|---|---|
| 1 | [Layout and indexing](#1-array-layout-and-indexing) | One-based. Bidirectional at 1, 3, 5, 7; omni at 2, 4, 6 | Counts **confirmed**; positions **derived** | A different array |
| 2 | [Array origin](#2-array-origin) | Centred on the array midpoint | **Stated** [Letter] | Jacobi–Anger: up to 1.7 dB WNG at 3.5 kHz. Exact design: none |
| 3 | [Phase sign](#3-phase-sign-convention) | `+j`: `e^{+jωx cosθ sinφ / c}` | **Stated** [Letter] | None if design and evaluation agree. DF collapses to about −21 dB if mixed |
| 4 | [Speed of sound](#4-speed-of-sound) | 343 m/s | **Chosen** | About ±0.15 dB WNG per ±3 m/s. DF unchanged |
| 5 | [Directional response](#5-directional-response-and-orientation) | `g = p + (1−p)·cos(θ−α)·sin φ`, α = 90° | **Stated** [EUSIPCO], [Paper] | At α = 90° the bidirectional mics are silent at end-fire |
| 6 | [Design vs evaluation](#6-design-plane-target-pattern-and-evaluation) | Designed in the horizontal plane. DF averaged over the full sphere | **Stated** | 2D and 3D DF are different quantities |
| 7 | [Target pattern](#6-design-plane-target-pattern-and-evaluation) | 2nd-order supercardioid, nulls at ±106° and ±153° | **Stated** [Letter], [EUSIPCO] | Defines the design |
| 8 | [DF quadrature](#7-df-integration-grid) | 361 × 181 grid | **Chosen** | Below 10⁻⁵ dB |
| 9 | [WNG formula](#8-wng-definition) | `1/(hᴴh)` in dB | **Stated** [Paper] | At most 0.09 dB (Jacobi–Anger) |
| 10 | [Reference curve](#9-reference-data) | Conventional LSA at θs = 0° | **Confirmed** | The figure holds eight curves |

---

## 1. Array layout and indexing

**Choice.** One-based indices `m = 1…7`. Bidirectional microphones at `m = 1, 3, 5, 7`; omnidirectional at `m = 2, 4, 6`. Adjacent spacing 0.5 cm, aperture 3 cm. Microphones of the same type are 1 cm apart.

**Source.**

- Three omni + four bidirectional at 0.5 cm spacing is stated in [EUSIPCO]. The counts were **confirmed** by a co-author of [EUSIPCO] (personal communication, [DATE]).
- Positions are **derived**. The orientation vector in [EUSIPCO] has the form `[α₁, 0, α₃, 0, π−α₃, 0, π−α₁]`, which puts the four directional microphones at the odd positions. Given the confirmed counts and strict alternation, this is the only layout that fits. The co-author's confirmation covered the counts, not the positions.
- [Letter] writes its positions for M omni + (M−1) bidirectional, with omni at both ends. This array has the opposite majority, so the same interleaving rule is applied with the roles swapped. The result has six gaps of exactly 0.5 cm and a 3.0 cm aperture (checked in code).

**Why it matters.** "Odd-indexed" is ambiguous. In a 7-element array, the one-based odd positions `{1, 3, 5, 7}` are four elements, while the zero-based odd indices `{1, 3, 5}` are three. They are complementary sets. An array with omnidirectional microphones at one-based odd positions has **four omni + three bidirectional**, which is not the array confirmed by the authors. State counts, not parity.

**Ordering in code.** In the original single-file script, position and weight vectors are ordered by type (omni first, then bidirectional), not by array index. Sort by position before comparing against the table in the README.

---

## 2. Array origin

**Choice.** The array is centred on its midpoint: `x_m = (m − 4) × 0.5 cm`, so positions run from −1.5 cm to +1.5 cm.

**Source.** **Stated** in [Letter] §II: "The center of the array is chosen as the origin of the coordinate system."

**Why it matters.** The Jacobi–Anger series is expanded about the origin, so shifting the array changes the weights it produces. The exact null-constrained design is unaffected, because a shift multiplies each steering vector by a unit-modulus phase and leaves |B| and ‖h‖ unchanged.

| Design | f (Hz) | Centred: DF / WNG (dB) | Shifted by +1.5 cm: DF / WNG (dB) |
|---|---|---|---|
| Jacobi–Anger | 500 | 8.210 / −41.663 | 8.218 / −41.714 |
| Jacobi–Anger | 3500 | 8.069 / −8.611 | 8.459 / −10.342 |
| Exact | 500 | 8.211 / −41.672 | identical |
| Exact | 3500 | 8.005 / −8.524 | identical |

---

## 3. Phase sign convention

**Choice.** The steering vector uses `e^{+jωx cosθ sinφ / c}` everywhere: in the Jacobi–Anger design, the exact design, and the evaluation.

**Source.** **Stated** in [Letter] Eqs. (1)–(3), which use `+j`. The draft of [Paper] (Eq. 8) wrote `−j`. I did not independently check which sign [EUSIPCO] uses.

**Why it matters.** The two signs are complex conjugates of each other, so DF and WNG are identical provided design and evaluation use the *same* sign. Mixing them silently breaks the distortionless constraint:

| Design sign | Evaluation sign | f (Hz) | `‖B(θs) − 1‖` | DF (dB) | WNG (dB) |
|---|---|---|---|---|---|
| + | + | 500 | 2×10⁻⁴ | 8.210 | −41.663 |
| − | − | 500 | 2×10⁻⁴ | 8.210 | −41.663 |
| + | − | 500 | **0.968** | **−21.649** | −41.663 |
| + | − | 3500 | **0.961** | **−20.093** | −8.611 |

WNG does not change under mixing because it depends only on ‖h‖. Always check the distortionless error first. See [PITFALLS.md](PITFALLS.md#1).

**If you switch to `−j`:** the Jacobi–Anger design matrix rows change from `(−j)ⁿ Jₙ(ωx/c)` to `(+j)ⁿ Jₙ(ωx/c)`, from `e^{jμ cosθ} = Σ jⁿ Jₙ(μ) e^{jnθ}` ([Letter] Eq. 37). Flip both together.

---

## 4. Speed of sound

**Choice.** `c = 343 m/s`.

**Source.** **Chosen.** [Letter] says only "the speed of sound in air", and the draft of [Paper] gives no value. I did not check whether [EUSIPCO] states one.

**Why it matters.** The array enters only through `ωx/c`, so changing `c` by a factor `k` is equivalent to rescaling every frequency by `1/k`.

| c (m/s) | Context | WNG at 500 Hz (dB) | Δ vs 343 m/s |
|---|---|---|---|
| 331.3 | 0 °C | −41.062 | +0.60 dB |
| 340.0 | | −41.511 | +0.15 dB |
| **343.0** | **~20 °C (repo default)** | **−41.663** | **0** |
| 346.1 | 25 °C | −41.819 | −0.16 dB |

DF changes by less than 0.001 dB across this range. Low-frequency WNG scales roughly as f⁴ (12 dB per octave, visible in the results table), so shifting it by 8 dB would need `c` of about 215 m/s, which is not a physical value for air.

---

## 5. Directional response and orientation

**Choice.** Each microphone has response

```
g_m(θ, φ) = p_m + (1 − p_m) · cos(θ − α_m) · sin φ
```

with `p_m = 1` omnidirectional and `p_m = 0` a pure dipole. All four bidirectional microphones use `α_m = π/2` (90°).

**Source.** The response model is **stated** in [Paper] Eq. (7). `α = π/2` for all directional microphones in the conventional LSA is **stated** in [EUSIPCO], which describes them as oriented toward broadside.

**Why it matters.** With `α = π/2`, `cos(θ − π/2) = sin θ`, so `g = sin θ · sin φ`, which is **zero at the look direction** θ = 0. At end-fire the four bidirectional microphones therefore contribute nothing to the look-direction constraint, and (shown in [PITFALLS.md](PITFALLS.md#4)) the minimum-norm solution gives them exactly zero weight. If α were anything other than π/2, this would change.

---

## 6. Design plane, target pattern, and evaluation

**Target pattern.** A 2nd-order supercardioid, `B(θ) = Σₙ αₙ cos(n(θ − θs))`, with `(α₀, α₁, α₂) = (0.309, 0.484, 0.207)`, which sum to 1. Look direction `θs = 0°`, `φs = 90°`. Nulls at `θs ± 106°` and `θs ± 153°`.

**Source.** **Stated.** The coefficients and null angles appear in [Letter] §V (where the nulls are listed at θs + 106° and θs + 153°), and [EUSIPCO] lists nulls at θs ± 106° and θs ± 153°. At θs = 0 the pattern is mirror-symmetric, so the "+" nulls imply the "−" nulls.

**Design is two-dimensional; evaluation is three-dimensional.**

- The Jacobi–Anger design follows [Letter], which is derived in the horizontal plane only (φ = 90°). The weights never see other elevations.
- DF is evaluated over the **full sphere**, as in [Paper] §4.1. The [Letter]'s own DF (its Eq. 8) is an *azimuthal* average. The two are different quantities, so DF values from the [Letter]'s figures are not comparable with the DF reported here.

**Orders.** For order N = 2, [Letter] requires at least N + 1 = 3 omnidirectional and N = 2 bidirectional sensors. This array has 3 and 4. At θs = 0 the bidirectional target coefficients vanish to machine precision, because they are proportional to sin(nθs).

---

## 7. DF integration grid

**Choice.** The spherical average is a rectangle-rule sum on a uniform 361 (θ) × 181 (φ) grid, with θ ∈ [0°, 360°) and φ ∈ [10⁻⁴, π − 10⁻⁴] rad.

**Source.** **Chosen.** No source specifies the grid.

**Poles.** The integrand carries a `sin φ` weight, so the poles contribute zero. Including them (φ = 0 and π exactly) changes DF by about 3×10⁻⁷ dB. The 10⁻⁴ rad offset is a precaution so that code dividing by `sin φ` never hits 0/0. Nothing in this repository requires it.

**Convergence.** Error is measured against a Gauss–Legendre reference (720 × 200 nodes: DF = 8.209668 dB at 500 Hz, 8.068907 dB at 3500 Hz).

| Grid | Error at 500 Hz (dB) | Error at 3500 Hz (dB) |
|---|---|---|
| **361 × 181 (repo)** | **+7.3×10⁻⁶** | **+7.0×10⁻⁶** |
| 361 × 181, poles included | +7.6×10⁻⁶ | +7.2×10⁻⁶ |
| 91 × 46 | +1.2×10⁻⁴ | +1.1×10⁻⁴ |
| 721 × 361 | +1.8×10⁻⁶ | +1.7×10⁻⁶ |

Error falls about 16× when the grid is refined 4×, consistent with second-order convergence. The grid is not a source of any visible discrepancy.

---

## 8. WNG definition

**Choice.** `WNG = 1 / (hᴴh)`, reported as `10·log₁₀(WNG)`. DF is likewise `10·log₁₀(DF)`.

**Source.** **Stated** in [Paper] Eq. (23), valid under the distortionless constraint `hᴴd(θs) = 1`.

**Why it matters.** The exact design satisfies the constraint to about 10⁻¹⁵, so the simple and full forms (`|hᴴd|²/(hᴴh)`) agree. The Jacobi–Anger design truncates its series at order 2, so its look-direction error is 2×10⁻⁴ at 500 Hz, growing to 1×10⁻² at 3500 Hz. The full form is then lower than the simple form by 0.002 dB at 500 Hz and 0.090 dB at 3500 Hz. The repository reports the simple form, and `data/expected_results.csv` uses it.

---

## 9. Reference data

**Choice.** The published WNG and DF values come from the curve for the **conventional LSA at θs = 0°** (end-fire).

**Source.** **Confirmed.** The WNG figure in [EUSIPCO] (Fig. 6 in the version I read; check numbering against your copy) shows eight curves: LSA and LSA+ at steering angles 0°, 30°, 60°, and 90°. A co-author of [EUSIPCO] confirmed that the curve being read is the conventional LSA at 0° (personal communication, [DATE]).

**Digitization.** [EUSIPCO] does not tabulate numerical values, so reference values were extracted with WebPlotDigitizer (version [VERSION], [DATE]). [Paper] estimates the digitization uncertainty at 0.016 dB for WNG and 0.011 dB for DF. The digitized values are in `data/reference_digitized.csv`, with the source figure and curve name recorded per row.

**Why it matters.** The conventional LSA at 0° is the *least* robust of the eight curves. A reproduction that lands far above or below it should first check that it is comparing against the right line.

---

## Not specified by any source I had access to

- The speed of sound ([§4](#4-speed-of-sound)) and the DF integration grid ([§7](#7-df-integration-grid)).
- Whether the authors' implementation adds regularization (for example, diagonal loading). [Letter] does not mention it. See [STATUS.md](STATUS.md) for how this relates to the open WNG gap.

<!-- TODO before publishing: fill [DATE] (three times: two for the correspondence, one for the digitization) and [VERSION]. Ask the authors' permission to cite the correspondence as "personal communication". -->
