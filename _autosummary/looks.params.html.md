# looks.params

One parameter schema per effect: names, types, defaults and bounds, once.

An effect’s parameters used to live in three places that could drift: the
compiler lambdas (a default read with `params.get(name, DFLT)`), the
effect-level checks in `looks.compile` (ranges), and the research catalogue.
Unknown keys were ignored, so `colorbalance` with `shadow=` (singular)
compiled to an identity grade without a word.

[`EFFECT_PARAMS`](#looks.params.EFFECT_PARAMS) is the single declaration. It is read by
[`check_params()`](#looks.params.check_params) (`looks.compile` calls it before an implementation is
chosen, so every implementation of an effect accepts the same documents) and by
[`with_defaults()`](#looks.params.with_defaults) (`looks.compile` fills defaults before a compiler or
cost estimator runs, so the compilers read `p["sigma"]`, never a second copy
of the default). Keyed by EFFECT, never by implementation: two implementations
of one effect must not disagree on what an omitted parameter means (rule 29b),
and a check inside one compiler is a check the licence tier can switch off.

An effect with no entry here is unchecked: a caller’s own registered effects
are theirs to validate. A parameter declared without a default stays absent
when omitted, and the compiler decides (usually by refusing).

The checks refuse what ffmpeg would silently change or what is not a number:
`True` and `"0.5"` are not floats, `inf` and `nan` are not finite,
`7.9` is not a whole number (it would be emitted as `7`).

### Examples

```pycon
>>> check_params("grain", {"strength": 7})
>>> check_params("grain", {"strenght": 7})
Traceback (most recent call last):
...
looks.params.ParamError: grain: unknown parameter 'strenght'; it takes ['seed', 'strength']
>>> with_defaults("grain", {"seed": 3})["strength"]
8
```

### Module Attributes

| [`NO_DEFAULT`](#looks.params.NO_DEFAULT)           | A parameter with no default is left absent when omitted.                                                                                         |
|-----------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------|
| [`DFLT_VIGNETTE_ANGLE`](#looks.params.DFLT_VIGNETTE_ANGLE)  | Vignette half-angle, radians.                                                                                                                    |
| [`MAX_VIGNETTE_ANGLE`](#looks.params.MAX_VIGNETTE_ANGLE)   | `vignette` clips its angle to [0, PI/2] instead of refusing, so a larger one would compile to a picture nobody asked for.                        |
| [`MAX_BLUR_SIGMA`](#looks.params.MAX_BLUR_SIGMA)       | `gblur` refuses a larger sigma ("Result too large"; 9.0 and 6.1).                                                                                |
| [`DFLT_HALATION_TINT`](#looks.params.DFLT_HALATION_TINT)   | film halation is the red layer scattering back off the base.                                                                                     |
| [`MAX_GRAIN_STRENGTH`](#looks.params.MAX_GRAIN_STRENGTH)   | `noise`'s `alls` range is 0..100.                                                                                                                |
| [`DFLT_GRAIN_SEED`](#looks.params.DFLT_GRAIN_SEED)      | Pinned rather than ffmpeg's own default, for portability across builds.                                                                          |
| [`MAX_GRAIN_SEED`](#looks.params.MAX_GRAIN_SEED)       | `noise`'s `all_seed` tops out at INT_MAX; its `-1` (a random seed) is below the range on purpose, since a seed is what makes grain reproducible. |
| [`DFLT_WEAVE_AMPLITUDE`](#looks.params.DFLT_WEAVE_AMPLITUDE) | Gate-weave wander, in pixels either side of centre.                                                                                              |
| [`DFLT_WEAVE_FREQUENCY`](#looks.params.DFLT_WEAVE_FREQUENCY) | Horizontal and vertical wander, Hz.                                                                                                              |
| [`DFLT_INTERP`](#looks.params.DFLT_INTERP)          | `lut3d`'s interpolation.                                                                                                                         |
| [`MAX_CUBE_SIZE`](#looks.params.MAX_CUBE_SIZE)        | The largest `.cube` grid worth asking for (size\*\*3 entries; ffmpeg's own limit is 256).                                                        |
| [`INTERP_MODES`](#looks.params.INTERP_MODES)         | `lut3d`'s `interp` values.                                                                                                                       |
| [`MAX_POSTERIZE_LEVELS`](#looks.params.MAX_POSTERIZE_LEVELS) | One code value per level on an 8-bit channel; more levels than that is the identity, and an absurd count only makes a huge expression.           |
| [`MAX_FLATTEN_SPATIAL`](#looks.params.MAX_FLATTEN_SPATIAL)  | sigmaS 0..512, sigmaR 0..1, planes a 4-bit mask.                                                                                                 |
| [`CURVES_CHANNELS`](#looks.params.CURVES_CHANNELS)      | `looks` channel names to ffmpeg `curves` option names.                                                                                           |
| [`COLORBALANCE_ZONES`](#looks.params.COLORBALANCE_ZONES)   | `colorbalance` tonal zones, keyed to the letter its options end in.                                                                              |
| [`EFFECT_PARAMS`](#looks.params.EFFECT_PARAMS)        | Effect -> its parameters.                                                                                                                        |
| [`PARAM_HINTS`](#looks.params.PARAM_HINTS)          | A refused key that deserves more than "unknown parameter".                                                                                       |

### Functions

| [`anything`](#looks.params.anything)(name[, default])                       | A key the effect takes whose shape its compiler owns (a path, a size, a ramp).   |
|--------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| [`as_emitted`](#looks.params.as_emitted)(value)                               | A number as the compilers write it into a filter string, read back.              |
| [`check_params`](#looks.params.check_params)(effect, params, \*[, schemas])     | Refuse an unknown key or a value the effect could not honour.                    |
| [`choice`](#looks.params.choice)(name, options[, default])                | One of a closed set of strings (an ffmpeg option's enum).                        |
| [`curve`](#looks.params.curve)(name)                                     | At least two `(x, y)` points in 0..1 with x strictly increasing.                 |
| [`flag`](#looks.params.flag)(name[, default])                           | A bool, not truthiness: `"false"` would otherwise be true.                       |
| [`real`](#looks.params.real)(name[, default, low, high, low_open, ...]) | A finite number, optionally bounded.                                             |
| `text`(name[, default])                                                                          |                                                                                  |
| [`vector`](#looks.params.vector)(name, length[, default, low, high])      | `length` finite numbers, each optionally bounded.                                |
| [`whole`](#looks.params.whole)(name[, default, low, high])               | A whole number (`8.0` is fine, `7.9` and `True` are not).                        |
| [`with_defaults`](#looks.params.with_defaults)(effect, params, \*[, schemas])    | The parameters with every declared default filled in; the input is untouched.    |

### Classes

| [`Param`](#looks.params.Param)(name, accepts, expects[, default, ...])   | One named parameter: how to recognise a valid value, and what omitted means.   |
|--------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|

### Exceptions

| [`ParamError`](#looks.params.ParamError)   | Parameters no implementation of an effect could honour.   |
|---------------------------------------------------------------|-----------------------------------------------------------|

### looks.params.COLORBALANCE_ZONES *= {'highlights': 'h', 'midtones': 'm', 'shadows': 's'}*

`colorbalance` tonal zones, keyed to the letter its options end in.

### looks.params.CURVES_CHANNELS *= ('all', 'red', 'green', 'blue')*

`looks` channel names to ffmpeg `curves` option names.

### looks.params.DFLT_GRAIN_SEED *= 0*

Pinned rather than ffmpeg’s own default, for portability across builds.
Note `0` is a different picture from an unseeded `noise`.

### looks.params.DFLT_HALATION_TINT *= (1.0, 0.35, 0.2)*

film halation is the red layer scattering back off the base.

* **Type:**
  Red-orange

### looks.params.DFLT_INTERP *= 'tetrahedral'*

`lut3d`’s interpolation. `posterize` after it needs `nearest`; that is
the caller’s choice, so the default is the filter’s own.

### looks.params.DFLT_VIGNETTE_ANGLE *= 0.6283185307179586*

Vignette half-angle, radians.

### looks.params.DFLT_WEAVE_AMPLITUDE *= 2*

Gate-weave wander, in pixels either side of centre.

### looks.params.DFLT_WEAVE_FREQUENCY *= (3.44, 2.33)*

Horizontal and vertical wander, Hz. Incommensurate so the path never loops
visibly: the production’s `n*0.9` and `n*0.61` rad/frame, at 24 fps.

### looks.params.EFFECT_PARAMS *: [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Param](#looks.params.Param)]]* *= {'blur': {'sigma': Param(name='sigma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1024]', default=2, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'colorbalance': {'highlights': Param(name='highlights', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers'), 'midtones': Param(name='midtones', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers'), 'preserve_lightness': Param(name='preserve_lightness', accepts=<function flag.<locals>.<lambda>>, expects='must be True or False', default=False, kind='flag', is_type=<function Param.<lambda>>, type_expects=''), 'shadows': Param(name='shadows', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers')}, 'contrast': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must not be negative', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'curves': {'all': Param(name='all', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects=''), 'blue': Param(name='blue', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects=''), 'green': Param(name='green', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects=''), 'red': Param(name='red', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='')}, 'fill': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='')}, 'fit': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='')}, 'flatten': {'planes': Param(name='planes', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 15]', default=7, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number'), 'range': Param(name='range', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.05, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'spatial': Param(name='spatial', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 512]', default=60, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'gamma': {'gamma': Param(name='gamma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'gate_weave': {'amplitude': Param(name='amplitude', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, inf]', default=2, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number'), 'frequency': Param(name='frequency', accepts=<function vector.<locals>.<lambda>>, expects='must be 2 numbers, each in [0, inf]', default=(3.44, 2.33), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='2 finite numbers')}, 'gradient_map': {'contrast': Param(name='contrast', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'interp': Param(name='interp', accepts=<function choice.<locals>.<lambda>>, expects="must be one of ['nearest', 'trilinear', 'tetrahedral', 'pyramid', 'prism']", default='tetrahedral', kind='choice', is_type=<function Param.<lambda>>, type_expects=''), 'lift': Param(name='lift', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=0.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'size': Param(name='size', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [2, 129]', default=33, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number'), 'stops': Param(name='stops', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects=''), 'title': Param(name='title', accepts=<function text.<locals>.<lambda>>, expects='must be a string', default='looks_gradient_map', kind='text', is_type=<function Param.<lambda>>, type_expects='')}, 'grain': {'seed': Param(name='seed', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 2147483647]', default=0, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number'), 'strength': Param(name='strength', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 100]', default=8, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number')}, 'halation': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.5, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'sigma': Param(name='sigma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, 1024], as written to six decimals', default=24.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'threshold': Param(name='threshold', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.78, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'tint': Param(name='tint', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [0, inf]', default=(1.0, 0.35, 0.2), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers')}, 'levels': {'black': Param(name='black', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-1, 1]', default=0, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'white': Param(name='white', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-1, 1]', default=1, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'lut3d': {'cube': Param(name='cube', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects=''), 'interp': Param(name='interp', accepts=<function choice.<locals>.<lambda>>, expects="must be one of ['nearest', 'trilinear', 'tetrahedral', 'pyramid', 'prism']", default='tetrahedral', kind='choice', is_type=<function Param.<lambda>>, type_expects='')}, 'motion': {'fps': Param(name='fps', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=<object object>, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'keyframes': Param(name='keyframes', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects=''), 'output': Param(name='output', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='')}, 'posterize': {'levels': Param(name='levels', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [2, 256]', default=8, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number')}, 'saturation': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'sharpen': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-2, 5]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'stretch': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='')}, 'vignette': {'angle': Param(name='angle', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, 1.5707963267948966], as written to six decimals', default=0.6283185307179586, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}}*

Effect -> its parameters. Geometry’s `target`, `gradient_map`’s `size`
and `title`, and `motion`’s keyframes have their defaults (or refusals)
where the value is built: `looks.geometry`, `looks.lut`, `looks.motion`.

### looks.params.INTERP_MODES *= ('nearest', 'trilinear', 'tetrahedral', 'pyramid', 'prism')*

`lut3d`’s `interp` values.

### looks.params.MAX_BLUR_SIGMA *= 1024*

`gblur` refuses a larger sigma (“Result too large”; 9.0 and 6.1).

### looks.params.MAX_CUBE_SIZE *= 129*

The largest `.cube` grid worth asking for (size\*\*3 entries; ffmpeg’s own
limit is 256). The default and the title belong to `looks.lut`.

### looks.params.MAX_FLATTEN_SPATIAL *= 512*

sigmaS 0..512, sigmaR 0..1, planes a 4-bit mask.

* **Type:**
  `bilateral`’s ranges

### looks.params.MAX_GRAIN_SEED *= 2147483647*

`noise`’s `all_seed` tops out at INT_MAX; its `-1` (a random seed) is
below the range on purpose, since a seed is what makes grain reproducible.

### looks.params.MAX_GRAIN_STRENGTH *= 100*

`noise`’s `alls` range is 0..100.

### looks.params.MAX_POSTERIZE_LEVELS *= 256*

One code value per level on an 8-bit channel; more levels than that is the
identity, and an absurd count only makes a huge expression.

### looks.params.MAX_VIGNETTE_ANGLE *= 1.5707963267948966*

`vignette` clips its angle to [0, PI/2] instead of refusing, so a larger
one would compile to a picture nobody asked for.

### looks.params.NO_DEFAULT *= <object object>*

A parameter with no default is left absent when omitted.

### looks.params.PARAM_HINTS *: [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [str](https://docs.python.org/3/builtins/stdtypes.html#str)], [str](https://docs.python.org/3/builtins/stdtypes.html#str)]* *= {('grain', 'temporal'): "there is no 'temporal' switch: grain is always re-drawn per frame, because static noise reads as dirt on the lens, not as grain"}*

A refused key that deserves more than “unknown parameter”.

### *class* looks.params.Param(name, accepts, expects, default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One named parameter: how to recognise a valid value, and what omitted means.

`accepts` is the strategy; the constructors below ([`real()`](#looks.params.real),
[`whole()`](#looks.params.whole), [`flag()`](#looks.params.flag), `text()`, [`vector()`](#looks.params.vector), [`curve()`](#looks.params.curve),
[`anything()`](#looks.params.anything)) cover every kind the registered effects need.

#### is_type()

Is the value of the right TYPE, bounds aside? A wrong type is reported
as one, never as a bound it did not fail.

#### kind *: [str](https://docs.python.org/3/builtins/stdtypes.html#str)* *= 'any'*

What sort of value this is, so a caller (or a test) can select
parameters by it rather than by parsing `expects`.

### *exception* looks.params.ParamError

Bases: [`ValueError`](https://docs.python.org/3/builtins/exceptions.html#ValueError)

Parameters no implementation of an effect could honour.

### looks.params.anything(name, default=<object object>)

A key the effect takes whose shape its compiler owns (a path, a size, a ramp).

### looks.params.as_emitted(value)

A number as the compilers write it into a filter string, read back.

A parameter check compares this, not the value asked for: six decimals are
kept, so two curve x-points `1e-7` apart are written as one point, which
`curves` refuses, and a vignette `angle` of `1e-9` is written `0`.

```pycon
>>> as_emitted(1e-9)
0.0
>>> as_emitted(0.1234567)
0.123457
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### looks.params.check_params(effect, params, \*, schemas={'blur': {'sigma': Param(name='sigma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1024]', default=2, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'colorbalance': {'highlights': Param(name='highlights', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers'), 'midtones': Param(name='midtones', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers'), 'preserve_lightness': Param(name='preserve_lightness', accepts=<function flag.<locals>.<lambda>>, expects='must be True or False', default=False, kind='flag', is_type=<function Param.<lambda>>, type_expects=''), 'shadows': Param(name='shadows', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers')}, 'contrast': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must not be negative', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'curves': {'all': Param(name='all', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects=''), 'blue': Param(name='blue', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects=''), 'green': Param(name='green', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects=''), 'red': Param(name='red', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='')}, 'fill': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='')}, 'fit': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='')}, 'flatten': {'planes': Param(name='planes', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 15]', default=7, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number'), 'range': Param(name='range', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.05, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'spatial': Param(name='spatial', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 512]', default=60, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'gamma': {'gamma': Param(name='gamma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'gate_weave': {'amplitude': Param(name='amplitude', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, inf]', default=2, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number'), 'frequency': Param(name='frequency', accepts=<function vector.<locals>.<lambda>>, expects='must be 2 numbers, each in [0, inf]', default=(3.44, 2.33), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='2 finite numbers')}, 'gradient_map': {'contrast': Param(name='contrast', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'interp': Param(name='interp', accepts=<function choice.<locals>.<lambda>>, expects="must be one of ['nearest', 'trilinear', 'tetrahedral', 'pyramid', 'prism']", default='tetrahedral', kind='choice', is_type=<function Param.<lambda>>, type_expects=''), 'lift': Param(name='lift', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=0.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'size': Param(name='size', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [2, 129]', default=33, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number'), 'stops': Param(name='stops', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects=''), 'title': Param(name='title', accepts=<function text.<locals>.<lambda>>, expects='must be a string', default='looks_gradient_map', kind='text', is_type=<function Param.<lambda>>, type_expects='')}, 'grain': {'seed': Param(name='seed', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 2147483647]', default=0, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number'), 'strength': Param(name='strength', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 100]', default=8, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number')}, 'halation': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.5, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'sigma': Param(name='sigma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, 1024], as written to six decimals', default=24.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'threshold': Param(name='threshold', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.78, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'tint': Param(name='tint', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [0, inf]', default=(1.0, 0.35, 0.2), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers')}, 'levels': {'black': Param(name='black', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-1, 1]', default=0, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'white': Param(name='white', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-1, 1]', default=1, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'lut3d': {'cube': Param(name='cube', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects=''), 'interp': Param(name='interp', accepts=<function choice.<locals>.<lambda>>, expects="must be one of ['nearest', 'trilinear', 'tetrahedral', 'pyramid', 'prism']", default='tetrahedral', kind='choice', is_type=<function Param.<lambda>>, type_expects='')}, 'motion': {'fps': Param(name='fps', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=<object object>, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'keyframes': Param(name='keyframes', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects=''), 'output': Param(name='output', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='')}, 'posterize': {'levels': Param(name='levels', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [2, 256]', default=8, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number')}, 'saturation': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'sharpen': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-2, 5]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'stretch': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='')}, 'vignette': {'angle': Param(name='angle', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, 1.5707963267948966], as written to six decimals', default=0.6283185307179586, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}})

Refuse an unknown key or a value the effect could not honour.

An effect with no schema is not checked. Only present keys are checked:
an absent one takes its declared default, so a check never has a second
copy of it.

* **Raises:**
  [**ParamError**](#looks.params.ParamError) – Naming the effect, the key and what it expects.
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### looks.params.choice(name, options, default=<object object>)

One of a closed set of strings (an ffmpeg option’s enum).

### looks.params.curve(name)

At least two `(x, y)` points in 0..1 with x strictly increasing.

Checked as emitted: x-points closer than the six decimals the compiler
writes become one point, and `curves` refuses the curve. An empty value
is accepted, because the compiler skips an empty channel too.

### looks.params.flag(name, default=<object object>)

A bool, not truthiness: `"false"` would otherwise be true.

### looks.params.real(name, default=<object object>, \*, low=None, high=None, low_open=False, emitted=False)

A finite number, optionally bounded. `emitted` bounds it as written.

### looks.params.vector(name, length, default=<object object>, \*, low=None, high=None)

`length` finite numbers, each optionally bounded.

### looks.params.whole(name, default=<object object>, \*, low=None, high=None)

A whole number (`8.0` is fine, `7.9` and `True` are not).

### looks.params.with_defaults(effect, params, \*, schemas={'blur': {'sigma': Param(name='sigma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1024]', default=2, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'colorbalance': {'highlights': Param(name='highlights', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers'), 'midtones': Param(name='midtones', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers'), 'preserve_lightness': Param(name='preserve_lightness', accepts=<function flag.<locals>.<lambda>>, expects='must be True or False', default=False, kind='flag', is_type=<function Param.<lambda>>, type_expects=''), 'shadows': Param(name='shadows', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers')}, 'contrast': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must not be negative', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'curves': {'all': Param(name='all', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects=''), 'blue': Param(name='blue', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects=''), 'green': Param(name='green', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects=''), 'red': Param(name='red', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='')}, 'fill': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='')}, 'fit': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='')}, 'flatten': {'planes': Param(name='planes', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 15]', default=7, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number'), 'range': Param(name='range', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.05, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'spatial': Param(name='spatial', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 512]', default=60, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'gamma': {'gamma': Param(name='gamma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'gate_weave': {'amplitude': Param(name='amplitude', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, inf]', default=2, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number'), 'frequency': Param(name='frequency', accepts=<function vector.<locals>.<lambda>>, expects='must be 2 numbers, each in [0, inf]', default=(3.44, 2.33), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='2 finite numbers')}, 'gradient_map': {'contrast': Param(name='contrast', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'interp': Param(name='interp', accepts=<function choice.<locals>.<lambda>>, expects="must be one of ['nearest', 'trilinear', 'tetrahedral', 'pyramid', 'prism']", default='tetrahedral', kind='choice', is_type=<function Param.<lambda>>, type_expects=''), 'lift': Param(name='lift', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=0.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'size': Param(name='size', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [2, 129]', default=33, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number'), 'stops': Param(name='stops', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects=''), 'title': Param(name='title', accepts=<function text.<locals>.<lambda>>, expects='must be a string', default='looks_gradient_map', kind='text', is_type=<function Param.<lambda>>, type_expects='')}, 'grain': {'seed': Param(name='seed', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 2147483647]', default=0, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number'), 'strength': Param(name='strength', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 100]', default=8, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number')}, 'halation': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.5, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'sigma': Param(name='sigma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, 1024], as written to six decimals', default=24.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'threshold': Param(name='threshold', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.78, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'tint': Param(name='tint', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [0, inf]', default=(1.0, 0.35, 0.2), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers')}, 'levels': {'black': Param(name='black', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-1, 1]', default=0, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'white': Param(name='white', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-1, 1]', default=1, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'lut3d': {'cube': Param(name='cube', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects=''), 'interp': Param(name='interp', accepts=<function choice.<locals>.<lambda>>, expects="must be one of ['nearest', 'trilinear', 'tetrahedral', 'pyramid', 'prism']", default='tetrahedral', kind='choice', is_type=<function Param.<lambda>>, type_expects='')}, 'motion': {'fps': Param(name='fps', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=<object object>, kind='real', is_type=<function \_is_real>, type_expects='a finite number'), 'keyframes': Param(name='keyframes', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects=''), 'output': Param(name='output', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='')}, 'posterize': {'levels': Param(name='levels', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [2, 256]', default=8, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number')}, 'saturation': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'sharpen': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-2, 5]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}, 'stretch': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='')}, 'vignette': {'angle': Param(name='angle', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, 1.5707963267948966], as written to six decimals', default=0.6283185307179586, kind='real', is_type=<function \_is_real>, type_expects='a finite number')}})

The parameters with every declared default filled in; the input is untouched.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)
