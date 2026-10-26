# looks.frame_dependency

Can this effect flicker? Answered by measurement, not by judgement.

The flagship look’s central claim is that it is \*frame-independent by
construction\* — one fixed LUT, no temporal state — so it **cannot** flicker,
which is the failure mode of every per-frame palette quantiser and of the
non-commercial cartoon models. That claim is worth something only if it can be
checked, and it turns out to reduce to **two ffmpeg probes and a comparison**.

Two questions, two probes, and each isolates one hazard:

1. **Does the effect vary with time?** Apply it to a *looped still* and diff
   consecutive output frames. A constant input can only produce a changing
   output if the effect reads the clock or the frame index. Measured: `noise`
   with the `t` flag moves 82–85/255; `lut3d`, `curves`, `gblur`, `deband` and
   `noise` *without* `t` move 0.
2. **Does the effect adapt to frame content?** Apply it to a source whose
   *left half is constant* while its *right half changes*, then look only at the
   left half. A content-independent effect leaves it alone; one that adapts to
   global statistics changes it, because the statistics moved. Measured:
   `normalize` moves the constant half by **219/255**; `lut3d`, `curves`,
   `gblur` move 0.

Question 2 is the one that matters. **A content-adaptive effect flickers** —
its output for an unchanged pixel depends on what else is in the frame, so a
pixel that never moves still shimmers as the shot changes around it.

### Three things this probe gets wrong if you build it naively

Each cost a false reading before it was fixed, and each fails **silently**.

- \*\*The varying half must actually move the statistic the effect adapts to,
  and no single source moves them all.\*\* This is the deepest limitation here,
  and it is measured rather than theorised. A first version used `testsrc2`,
  which always spans the full luma range and therefore never moves a min/max —
  `normalize` read **0**, a false negative saying “cannot flicker” about an
  effect that can. A *fading* half moves the range and `normalize` jumps to
  **219**. But the fade leaves the colour histogram nearly alone, so `elbg` — a
  vector quantiser, adaptive by definition — still read **0**. A *hue-cycling*
  half moves the histogram and catches `elbg` at 5–8 — while missing
  `normalize` entirely, because it does not move the range.

  So **two** content probes run and the verdict is the larger. The pair is not
  provably complete: an effect adapting to a statistic neither probe moves
  reads independent. See *What this does not answer*.
- **Chroma subsampling bleeds across the seam.** In `yuv420p` a chroma sample
  is shared between the constant and varying halves, so the boundary column
  changes for reasons that have nothing to do with the effect. `yuv444p` plus a
  margin removes it.
- **\`tblend=difference\` of identical frames is not zero in RGB.** Black in
  limited-range YUV is 16, so a difference computed in RGB and then measured by
  `signalstats` reads 16 everywhere. Filters that need RGB (`lut3d`, `curves`)
  force that conversion, so the format is pinned on **both** sides of the
  effect under test.

### What this does not answer

**Some temporal filters.** A third probe (below) catches the common case by
running two sequences that differ only *before* a shared textured tail:
`tmix=frames=3` shows **146**/255 in the tail and `hqdn3d` shows 2. But
`tblend` and `atadenoise` both read **0** and are misreported as independent.
Measured, and the reason is structural rather than a tuning failure: `tblend`
consumes two input frames per output frame, so the trim that skips the
perturbation for a normal filter lands *past* it; `atadenoise` keeps nine
frames of history, more than a short probe can perturb. Lengthening the
perturbation from one frame to three changed neither — verified.

Those two are refused for an unrelated and stronger reason anyway: \*\*every
temporal filter is out of scope\*\*, because the execution model this package
serves renders one bounded ffmpeg *per cut*, so a temporal filter meets a hard
discontinuity at every cut. Do not read that as making the gap harmless —
it means the gap is not currently load-bearing, not that it is closed.

\*\*And an `INDEPENDENT` verdict is evidence, not proof.\*\* It says: none of three
probes could make this effect change a pixel it should not have touched. An
effect adapting to a statistic none of them moves would pass, and so would
`tblend`.
That is why the flagship look’s claim does **not** rest on this module — a
fixed per-pixel lookup with no state cannot depend on anything else, which is a
*structural* argument, and the measurement corroborates it rather than
substituting for it. Use [`classify()`](#looks.frame_dependency.classify) to catch an effect that flickers; do
not use it to certify one that does not, unless you also have the structural
argument.

Every process here goes through `looks._run`, and every one is an
`ffprobe` reading filter metadata — no pixel ever leaves ffmpeg, so the
`-f null -` invariant is preserved by construction rather than by care.

### Module Attributes

| [`PROBE_SIZE`](#looks.frame_dependency.PROBE_SIZE)               | Probe geometry.                                                     |
|---------------------------------------------------------------------------|---------------------------------------------------------------------|
| [`SEAM_MARGIN`](#looks.frame_dependency.SEAM_MARGIN)              | How far in from the seam the constant half is sampled, in pixels.   |
| [`NOISE_FLOOR`](#looks.frame_dependency.NOISE_FLOOR)              | A difference at or below this (out of 255) is treated as no change. |
| [`UNDETERMINED`](#looks.frame_dependency.UNDETERMINED)             | Convenience alias for the value that means "no answer".             |
| [`FLICKER_FREE`](#looks.frame_dependency.FLICKER_FREE)             | The classes that cannot produce flicker.                            |
| [`DETERMINISM_PROBE_FRAMES`](#looks.frame_dependency.DETERMINISM_PROBE_FRAMES) | How many frames the determinism probe examines.                     |
| [`TEMPORAL_PROBE_FRAMES`](#looks.frame_dependency.TEMPORAL_PROBE_FRAMES)    | How many frames of the shared tail the temporal probe examines.     |

### Functions

| [`assert_flicker_free`](#looks.frame_dependency.assert_flicker_free)(chain, \*\*kwargs)   | Raise unless `chain` provably cannot flicker.   |
|-------------------------------------------------------------------------------------------|-------------------------------------------------|
| [`classify`](#looks.frame_dependency.classify)(chain, \*[, ffprobe, timeout])  | Measure what `chain` depends on.                |

### Classes

| [`Dependency`](#looks.frame_dependency.Dependency)(\*values)                            | What an effect's output depends on, worst case.         |
|--------------------------------------------------------------------------------------------------|---------------------------------------------------------|
| [`DependencyReport`](#looks.frame_dependency.DependencyReport)(dependency[, time_delta, ...]) | What the two probes measured, and what follows from it. |

### looks.frame_dependency.DETERMINISM_PROBE_FRAMES *= 20*

How many frames the determinism probe examines.

**Twenty, and the number is measured rather than chosen.** Detecting
randomness is itself probabilistic: two runs of a stochastic filter can agree
by chance, and the more frames you compare the less likely that is across all
of them. On `elbg` (a vector quantiser whose default `seed=-1` re-randomises
every instantiation), detection rate over eight repeats:

> 3 frames -> 1/6      8 frames -> 7/8      20 frames -> 8/8      40 -> 8/8

An earlier six-repeat sample read 6/6 at eight frames and set the constant
there; a fuller sample found 7/8, and the flake surfaced as an intermittent
test. **That is the same probabilistic-detection point one level up** — a
small sample can agree by chance too.

The consequence, and it is the honest framing of this whole verdict: a
`NONDETERMINISTIC` result is a proof, but its **absence is not**. An effect
random in one pixel per ten thousand would pass at any frame count here.

### *class* looks.frame_dependency.Dependency(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

What an effect’s output depends on, worst case.

Ordered by how badly each behaves across a cut:

- `INDEPENDENT` — the same input pixel gives the same output pixel,
  always. Cannot flicker. This is what the flagship look is.
- `INDEPENDENT` — no probe could make the effect touch a pixel it
  should not have. **Evidence, not proof** — see the module docstring.
  A pixel-local map and a small spatial filter both land here, and for the
  flicker question that is the right grouping: neither can flicker.
- `TIME_VARYING` — output depends on the frame index or clock.
  Deterministic and reproducible, but it changes: film grain is the wanted
  case.
- `CONTENT_ADAPTIVE` — output depends on the frame’s global
  statistics. **This flickers**, and it is the class the whole
  frame-independence argument is about.
- `TEMPORAL` — output at frame *n* depends on frames before it.
  Structurally incompatible with the execution model this package serves:
  the consumer renders one bounded ffmpeg **per cut**, so a temporal filter
  meets a hard discontinuity at every cut and produces an artefact at every
  one of them.
- `NONDETERMINISTIC` — two applications of the effect to the SAME
  input disagree. A reproducibility hazard rather than a flicker one: a
  re-render produces a different picture. Detected first, because it
  invalidates every other probe here.
- [`UNDETERMINED`](#looks.frame_dependency.UNDETERMINED) — a probe could not run. Never a synonym for
  independent.

### *class* looks.frame_dependency.DependencyReport(dependency, time_delta=None, content_delta=None, temporal_delta=None, determinism_delta=None, note='')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What the two probes measured, and what follows from it.

#### dependency

The verdict.

* **Type:**
  [`Dependency`](#looks.frame_dependency.Dependency)

#### time_delta

Largest change between consecutive output frames on a
constant input, out of 255.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### content_delta

Largest change in the constant half when the rest of the
frame changed, out of 255.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### temporal_delta

Largest change in a shared tail when the frames BEFORE
it differed, out of 255.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### determinism_delta

Largest disagreement between two applications of the
effect to the SAME input, out of 255. Nonzero means the effect is
random, and every other number in this report is then meaningless.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### can_flicker

Whether the verdict admits flicker. `None` when
undetermined — **not** `False`, because “we could not tell” and
“it cannot” are different answers and only one of them is a
guarantee.

#### note

Why, when something could not be measured.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.frame_dependency.FLICKER_FREE *= frozenset({Dependency.INDEPENDENT})*

The classes that cannot produce flicker.

### looks.frame_dependency.NOISE_FLOOR *= 1*

A difference at or below this (out of 255) is treated as no change.
Not zero: a filter that round-trips through another pixel format can move a
value by one without depending on anything.

### looks.frame_dependency.PROBE_SIZE *= (32, 64)*

Probe geometry. Small on purpose — the classification is about *whether* a
value changes, not by how much, so resolution buys nothing and costs time.

### looks.frame_dependency.SEAM_MARGIN *= 12*

How far in from the seam the constant half is sampled, in pixels.

A spatial effect legitimately reads pixels near the boundary, so without a
margin every blur reads as content-adaptive. The margin cannot be made large
enough for *every* spatial effect — a Gaussian’s support runs to about 3
sigma, so `gblur=sigma=4` crosses 8 px and `sigma=10` would cross any margin
this probe can afford.

That residual error is **conservative**: an over-wide spatial filter is
reported as `CONTENT_ADAPTIVE`, i.e. “can flicker” about something that
cannot. For a refusal engine that is the safe direction — the unsafe one is
calling an adaptive effect independent. Widen the margin (and the probe) if a
specific broad filter needs a correct verdict.

### looks.frame_dependency.TEMPORAL_PROBE_FRAMES *= 3*

How many frames of the shared tail the temporal probe examines.

Small on purpose, and this is the subtle part: the probe only detects a
temporal effect if the frames it samples still have the perturbation inside
their memory window. Trimming further in makes every temporal filter read as
independent — measured, `tmix=frames=3` read 0 when sampling began 3 frames
after the perturbation and 146/255 when it began 1 frame after.

### looks.frame_dependency.UNDETERMINED *= Dependency.UNDETERMINED*

Convenience alias for the value that means “no answer”.

### looks.frame_dependency.assert_flicker_free(chain, \*\*kwargs)

Raise unless `chain` provably cannot flicker.

\*\*What a pass means, precisely: three probes could not make this effect
depend on anything they varied.\*\* It is not a proof of frame independence —
`tblend` and `atadenoise` pass and are temporal. For an effect whose class
matters, pair this with the structural argument (a stateless per-pixel
lookup cannot depend on anything else) or with a declared class this
function is used to *falsify*.

An `UNDETERMINED` verdict **raises**: “we could not tell” must not be
reported as “it cannot”, which is the same unknown-is-a-refusal rule the
licence tier follows, applied to the other guarantee this package makes.

* **Raises:**
  [**AssertionError**](https://docs.python.org/3/builtins/exceptions.html#AssertionError) – The chain can flicker, or could not be shown not to.
* **Return type:**
  [`DependencyReport`](#looks.frame_dependency.DependencyReport)

### looks.frame_dependency.classify(chain, , ffprobe='ffprobe', timeout=120.0)

Measure what `chain` depends on.

* **Parameters:**
  * **chain** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – An ffmpeg filter chain, as it would appear in `-vf`.
  * **ffprobe** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Binary name or path.
  * **timeout** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – Seconds per probe.
* **Return type:**
  [`DependencyReport`](#looks.frame_dependency.DependencyReport)

### Examples

```pycon
>>> classify('lut3d=look.cube').dependency
<Dependency.INDEPENDENT: 'independent'>
>>> classify('normalize').can_flicker
True
```
