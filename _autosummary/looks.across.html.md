# looks.across

Choosing one parameter per clip so a SET looks consistent — exactly, not by search.

The measured rule this mechanises: a single global flattening scale made the
softest of three sources softer still, so it became the softest thing on screen.
Per-clip choice beat it — \*\*2.004x against uniform’s 2.213x and
sharpest-everywhere’s 2.364x\*\* — where the number is the ratio between the
brightest and dimmest post-effect measurement across the set. Lower is more
consistent.

So the question is: given a grid of candidate parameter values per clip, and a
measurement of what each candidate produces, which value does each clip get?

### It is closed-form, and the closed form matters

Reaching for the exhaustive product is the natural move and it is hopeless:

```
|G|^|S|
```

 is **8³⁰ ≈ 1.24 x 10²⁷** at the documented size. But the problem is the
classic *narrowest window containing one element from each of N sorted lists*,
which a single sorted sweep with two pointers answers exactly. Measured here:
**0.093 ms at N=30, |G|=8**, and 4000 randomised trials against brute force with
ties, duplicates and repeated values across lists — **zero disagreements**.

### Why logs

Minimising the spread of `log(x)` *is* minimising the ratio `max/min` — the
same objective, the same chosen values, verified. Logs are what turn a ratio
into a difference, which is what a sweep can add up. The consequence worth
having is that the objective is **scale-independent**: multiply every
measurement by a thousand and the answer does not move.

The consequence worth refusing is that `log(0)` does not exist, and a
Laplacian variance genuinely can be 0 on a flat clip. So a non-positive
measurement is a refusal. Clamping it to a small epsilon would be inventing a
measurement, which is the one thing this package will not do.

### Why the dispersion functional is a separate field

`max/min` is defensible at N=3 and fragile at N=30, because one clip that
cannot be fixed sets the whole window. Measured, with 29 clips that can all land
near one value and a thirtieth whose entire grid sits ten times away:

| functional             | ratio      |
|------------------------|------------|
| every clip (max/min)   | **9.026x** |
| dropping the worst one | **1.037x** |

The outlier accounts for **98.3%** of the log window, and the other 29 clips’
whole remaining freedom moves the objective by about 13%. Their choices have
stopped mattering.

And the trim costs no exactness — that is the point. “Narrowest window covering
at least N-k of the lists” is the same sweep with a `>=` in place of an `==`,
and it agreed with brute force over 1500 trials. So the functional is a field
rather than a fork.

### What this module does not do

It does not measure. [`looks.measure`](looks.html.md#looks.measure) does that, by running ffmpeg, and
[`looks.resolve_across()`](looks.html.md#looks.resolve_across) applies the answer. This is the arithmetic in
between: measurements in, one value per clip out.

### Module Attributes

| [`Objective`](#looks.across.Objective)   | there is no honest reason to *maximise* the spread of a set's appearance, and a one-member Literal makes asking for it unrepresentable rather than merely unwise.   |
|--------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`Statistic`](#looks.across.Statistic)   | Which measurement to make consistent.                                                                                                                               |
| [`Dispersion`](#looks.across.Dispersion)  | How the spread of the chosen values is summarised.                                                                                                                  |

### Functions

| [`probes_for`](#looks.across.probes_for)(spread, parameter)                  | A [`Spread`](#looks.across.Spread) as the probes [`looks.resolve_across()`](looks.html.md#looks.resolve_across) takes.   |
|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`solve_across`](#looks.across.solve_across)(candidates, \*[, statistic, ...]) | One parameter value per clip, so the set's measurements sit close together.                                                                                                   |

### Classes

| [`Candidate`](#looks.across.Candidate)(value, stats)                        | One candidate parameter value, and what it measured.                 |
|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [`Choice`](#looks.across.Choice)(source_id, value, statistic)            | The value one clip was given, and the measurement that justifies it. |
| [`Spread`](#looks.across.Spread)(choices, ratio, log_spread, ...[, ...]) | The answer: one choice per clip, and how consistent the set now is.  |

### Exceptions

| [`AcrossError`](#looks.across.AcrossError)   | A set-relative question that cannot be answered as asked.   |
|----------------------------------------------------------------|-------------------------------------------------------------|

### *exception* looks.across.AcrossError

Bases: [`MeasurementError`](looks.html.md#looks.MeasurementError)

A set-relative question that cannot be answered as asked.

### *class* looks.across.Candidate(value, stats)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One candidate parameter value, and what it measured.

`value` is whatever the parameter is — a flattening scale, a sigma, a
level count. It is carried opaquely: this module compares *measurements*,
never parameters.

### *class* looks.across.Choice(source_id, value, statistic)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The value one clip was given, and the measurement that justifies it.

### looks.across.Dispersion

How the spread of the chosen values is summarised.

`full_range` is `max/min` over every clip. `trimmed_range` allows
`drop` clips to sit outside the window, which is what keeps one unfixable
clip from setting the objective for the other twenty-nine. Both are solved
exactly by the same sweep.

alias of [`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[‘full_range’, ‘trimmed_range’]

### looks.across.Objective

there is no honest
reason to *maximise* the spread of a set’s appearance, and a one-member
Literal makes asking for it unrepresentable rather than merely unwise.

* **Type:**
  The objective. **Exactly one member, deliberately**

alias of [`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[‘min_spread’]

### *class* looks.across.Spread(choices, ratio, log_spread, dispersion, statistic, outside=())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The answer: one choice per clip, and how consistent the set now is.

`ratio` is the headline — the same number the measured rule is quoted in,
so a caller can compare it against uniform’s 2.213x directly. It is
`exp(log_spread)` and the two are reported together because the first is
what a person reads and the second is what the solver minimised.

#### outside *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), ...]* *= ()*

Clips the trim left outside the window. Empty under `full_range`.
Named rather than counted, because *which* clip could not be fixed is
the interesting half of the answer.

### looks.across.Statistic

Which measurement to make consistent. Closed, because the objective is a
RATIO and only a positive-valued statistic has one — an offset-valued field
would give a ratio that changes when the offset does.

alias of [`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[‘sharpness’, ‘blur’]

### looks.across.probes_for(spread, parameter)

A [`Spread`](#looks.across.Spread) as the probes [`looks.resolve_across()`](looks.html.md#looks.resolve_across) takes.

The join between the two halves of RULE N: this module answers the
set-relative question, and `resolve_across` applies the answer, turning
each `SET_RELATIVE` Look into an `EXTERNAL` one that will not be asked
again against a different set.

* **Parameters:**
  **parameter** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The [`Ref`](looks.spec.html.md#looks.spec.Ref) key the value fills in.
* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### Examples

```pycon
>>> spread = Spread(choices=(Choice('c01', 0.75, 40.0),
...                          Choice('c02', 0.5, 42.0)),
...                 ratio=1.05, log_spread=0.049,
...                 dispersion='full_range', statistic='sharpness')
>>> probes_for(spread, 'scale')
({'scale': 0.75}, {'scale': 0.5})
```

### looks.across.solve_across(candidates, , statistic='sharpness', objective='min_spread', dispersion='full_range', drop=0)

One parameter value per clip, so the set’s measurements sit close together.

* **Parameters:**
  * **candidates** ([`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`Candidate`](#looks.across.Candidate)]]) – `{source_id: [Candidate, ...]}` — the grid, already
    measured. This module does not measure; see [`looks.measure`](looks.html.md#looks.measure).
  * **statistic** ([`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'sharpness'`, `'blur'`]) – Which measurement to make consistent.
  * **objective** ([`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'min_spread'`]) – `"min_spread"`, and only that. See [`Objective`](#looks.across.Objective).
  * **dispersion** ([`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'full_range'`, `'trimmed_range'`]) – `"full_range"` (max/min over every clip) or
    `"trimmed_range"` (allow `drop` clips outside the window).
  * **drop** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – How many clips may sit outside. Only with `trimmed_range`.
* **Raises:**
  [**AcrossError**](#looks.across.AcrossError) – If the inputs cannot yield an answer — no clips, a clip
      with an empty grid, measurements that are not comparable with each
      other, a missing or non-positive statistic, or a `drop` that would
      leave nothing to be consistent about.
* **Return type:**
  [`Spread`](#looks.across.Spread)

### Examples

Three clips, each with two candidates. The solver picks the combination
whose measurements sit closest together, not the sharpest one each:

```pycon
>>> def stats(source_id, sharpness):
...     return ClipStats(source_id=source_id, stage='post_effect',
...                      instrument='x', luma_space='coded_y',
...                      sample_spec='uniform:5', n_frames=5,
...                      sharpness=sharpness)
>>> got = solve_across({
...     'c01': [Candidate(0.5, stats('c01', 100.0)),
...             Candidate(0.75, stats('c01', 40.0))],
...     'c02': [Candidate(0.5, stats('c02', 42.0)),
...             Candidate(0.75, stats('c02', 20.0))],
...     'c03': [Candidate(0.5, stats('c03', 38.0)),
...             Candidate(0.75, stats('c03', 12.0))],
... })
>>> [(c.source_id, c.value) for c in got.choices]
[('c01', 0.75), ('c02', 0.5), ('c03', 0.5)]
>>> round(got.ratio, 3)
1.105
```

Choosing the sharpest everywhere would have been far worse:

```pycon
>>> round(100.0 / 38.0, 3)
2.632
```
