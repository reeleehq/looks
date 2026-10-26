# looks.stages

The canonical stage order, and a check that warns when a Look departs from it.

The effect catalogue (`docs/research/13` §1.3) states an order that is
load-bearing rather than aesthetic:

```default
geometry -> grade -> flatten -> look (LUT, posterize) -> optical -> grain
```

Five measured constraints sit behind it: nothing that resamples after
`posterize` (downscale-after-posterize left 359 distinct colours where
downscale-before left 77); `flatten` before the LUT; `grain` last (before a
LUT it is colour-mapped, before `posterize` it is quantised away); optical
effects after the look; `deband` before `posterize`.

`looks` **validates and warns, never reorders**: the order asked for is the
order compiled, and a departure from the canon is sometimes deliberate. The
stage is a property of *what an effect does*, so it is declared here per
effect, never per implementation (the same rule that puts parameter checks in
`looks.compile` rather than inside a compiler). An effect with no stage is
unconstrained, and the table is an argument of [`check_stage_order()`](#looks.stages.check_stage_order).

Callers who want a refusal rather than a warning escalate the category:
`warnings.simplefilter("error", StageOrderWarning)`.

### Examples

```pycon
>>> from looks.spec import Effect
>>> check_stage_order([Effect(name="grain"), Effect(name="lut3d")])
['lut3d (stage look) follows grain (stage grain); the canonical order is geometry -> grade -> flatten -> look -> optical -> grain']
>>> check_stage_order([Effect(name="lut3d"), Effect(name="grain")])
[]
```

### Module Attributes

| [`EFFECT_STAGES`](#looks.stages.EFFECT_STAGES)      | Effect name -> stage.                                                                           |
|---------------------------------------------------------------------|-------------------------------------------------------------------------------------------------|
| [`RESAMPLING_EFFECTS`](#looks.stages.RESAMPLING_EFFECTS) | Effects that resample, interpolate or smooth the picture, and so manufacture in-between values. |
| [`QUANTISER`](#looks.stages.QUANTISER)          | The effect after which nothing may resample.                                                    |

### Functions

| [`check_stage_order`](#looks.stages.check_stage_order)(effects, \*[, stages, ...])   | Describe each departure from the canonical order; empty when there is none.   |
|--------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------|

### Classes

| [`Stage`](#looks.stages.Stage)(\*values)   | Pipeline stages, in canonical order.   |
|--------------------------------------------------------------------|----------------------------------------|

### Exceptions

| [`StageOrderWarning`](#looks.stages.StageOrderWarning)   | A Look puts an effect in a stage the catalogue measured as wrong.   |
|----------------------------------------------------------------------|---------------------------------------------------------------------|

### looks.stages.EFFECT_STAGES *: [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Stage](#looks.stages.Stage)]* *= {'colorbalance': Stage.GRADE, 'contrast': Stage.GRADE, 'curves': Stage.GRADE, 'fill': Stage.GEOMETRY, 'fit': Stage.GEOMETRY, 'flatten': Stage.FLATTEN, 'gamma': Stage.GRADE, 'gradient_map': Stage.LOOK, 'grain': Stage.GRAIN, 'halation': Stage.OPTICAL, 'levels': Stage.GRADE, 'lut3d': Stage.LOOK, 'motion': Stage.GEOMETRY, 'posterize': Stage.LOOK, 'saturation': Stage.GRADE, 'stretch': Stage.GEOMETRY, 'vignette': Stage.OPTICAL}*

Effect name -> stage. An effect absent from here is unconstrained.

### looks.stages.QUANTISER *= 'posterize'*

The effect after which nothing may resample.

### looks.stages.RESAMPLING_EFFECTS *= frozenset({'blur', 'fill', 'fit', 'gate_weave', 'gradient_map', 'lut3d', 'motion', 'sharpen', 'stretch'})*

Effects that resample, interpolate or smooth the picture, and so manufacture
in-between values. After `posterize` they un-quantise it. Includes the LUT
effects (posterise-then-LUT: 96 distinct colours against LUT-then-posterise’s
51, note 05) and `gate_weave`, which has no stage but still resamples.

### *class* looks.stages.Stage(\*values)

Bases: [`IntEnum`](https://docs.python.org/3/library/enum.html#enum.IntEnum)

Pipeline stages, in canonical order.

### *exception* looks.stages.StageOrderWarning

Bases: [`UserWarning`](https://docs.python.org/3/builtins/exceptions.html#UserWarning)

A Look puts an effect in a stage the catalogue measured as wrong.

### looks.stages.check_stage_order(effects, , stages={'colorbalance': Stage.GRADE, 'contrast': Stage.GRADE, 'curves': Stage.GRADE, 'fill': Stage.GEOMETRY, 'fit': Stage.GEOMETRY, 'flatten': Stage.FLATTEN, 'gamma': Stage.GRADE, 'gradient_map': Stage.LOOK, 'grain': Stage.GRAIN, 'halation': Stage.OPTICAL, 'levels': Stage.GRADE, 'lut3d': Stage.LOOK, 'motion': Stage.GEOMETRY, 'posterize': Stage.LOOK, 'saturation': Stage.GRADE, 'stretch': Stage.GEOMETRY, 'vignette': Stage.OPTICAL}, resampling=frozenset({'blur', 'fill', 'fit', 'gate_weave', 'gradient_map', 'lut3d', 'motion', 'sharpen', 'stretch'}), quantiser='posterize')

Describe each departure from the canonical order; empty when there is none.

Each message names the offending (later) effect once, against the first
earlier effect that belongs after it.

### Examples

```pycon
>>> from looks.spec import Effect
>>> check_stage_order([Effect(name="posterize"), Effect(name="fit")])
['fit resamples the picture after posterize...']
>>> check_stage_order([Effect(name="fit"), Effect(name="saturation"), Effect(name="grain")])
[]
```

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]
