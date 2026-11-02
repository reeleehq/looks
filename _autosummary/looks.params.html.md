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

| [`NO_DEFAULT`](#looks.params.NO_DEFAULT)              | A parameter with no default is left absent when omitted.                                                                                                                                            |
|--------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`DFLT_VIGNETTE_ANGLE`](#looks.params.DFLT_VIGNETTE_ANGLE)     | Vignette half-angle, radians.                                                                                                                                                                       |
| [`MAX_VIGNETTE_ANGLE`](#looks.params.MAX_VIGNETTE_ANGLE)      | `vignette` clips its angle to [0, PI/2] instead of refusing, so a larger one would compile to a picture nobody asked for.                                                                           |
| [`MAX_BLUR_SIGMA`](#looks.params.MAX_BLUR_SIGMA)          | `gblur` refuses a larger sigma ("Result too large"; 9.0 and 6.1).                                                                                                                                   |
| [`DFLT_HALATION_TINT`](#looks.params.DFLT_HALATION_TINT)      | film halation is the red layer scattering back off the base.                                                                                                                                        |
| [`MAX_GRAIN_STRENGTH`](#looks.params.MAX_GRAIN_STRENGTH)      | `noise`'s `alls` range is 0..100.                                                                                                                                                                   |
| [`DFLT_GRAIN_SEED`](#looks.params.DFLT_GRAIN_SEED)         | Pinned rather than ffmpeg's own default, for portability across builds.                                                                                                                             |
| [`MAX_GRAIN_SEED`](#looks.params.MAX_GRAIN_SEED)          | `noise`'s `all_seed` tops out at INT_MAX; its `-1` (a random seed) is below the range on purpose, since a seed is what makes grain reproducible.                                                    |
| [`DFLT_WEAVE_AMPLITUDE`](#looks.params.DFLT_WEAVE_AMPLITUDE)    | Gate-weave wander, in pixels either side of centre.                                                                                                                                                 |
| [`DFLT_WEAVE_FREQUENCY`](#looks.params.DFLT_WEAVE_FREQUENCY)    | Horizontal and vertical wander, Hz.                                                                                                                                                                 |
| [`DFLT_INTERP`](#looks.params.DFLT_INTERP)             | `lut3d`'s interpolation.                                                                                                                                                                            |
| [`MAX_CUBE_SIZE`](#looks.params.MAX_CUBE_SIZE)           | The largest `.cube` grid worth asking for (size\*\*3 entries; ffmpeg's own limit is 256).                                                                                                           |
| [`INTERP_MODES`](#looks.params.INTERP_MODES)            | `lut3d`'s `interp` values.                                                                                                                                                                          |
| [`MAX_POSTERIZE_LEVELS`](#looks.params.MAX_POSTERIZE_LEVELS)    | One code value per level on an 8-bit channel; more levels than that is the identity, and an absurd count only makes a huge expression.                                                              |
| [`MAX_FLATTEN_SPATIAL`](#looks.params.MAX_FLATTEN_SPATIAL)     | sigmaS 0..512, sigmaR 0..1, planes a 4-bit mask.                                                                                                                                                    |
| [`DFLT_RIPPLE_AMPLITUDE`](#looks.params.DFLT_RIPPLE_AMPLITUDE)   | The ripple warp (issue #49), normalised so one look reads the same at any size.                                                                                                                     |
| [`DFLT_RIPPLE_WAVELENGTHS`](#looks.params.DFLT_RIPPLE_WAVELENGTHS) | The two ripple harmonics' wavelengths, as fractions of the frame's height.                                                                                                                          |
| [`DFLT_RIPPLE_BLOOM`](#looks.params.DFLT_RIPPLE_BLOOM)       | Peak weight of the blurred, brightened copy mixed in at the middle.                                                                                                                                 |
| [`CURVES_CHANNELS`](#looks.params.CURVES_CHANNELS)         | `looks` channel names to ffmpeg `curves` option names.                                                                                                                                              |
| [`COLORBALANCE_ZONES`](#looks.params.COLORBALANCE_ZONES)      | `colorbalance` tonal zones, keyed to the letter its options end in.                                                                                                                                 |
| [`DEPTH_CARRIED_FORMATS`](#looks.params.DEPTH_CARRIED_FORMATS)   | Formats whose bit depth survives a step registered with `keeps_depth` (`EffectRegistry.register`), so `compile_look` may carry the clip's format past such a step for the depth checks (issue #52). |
| [`EFFECT_PARAMS`](#looks.params.EFFECT_PARAMS)           | Effect -> its parameters.                                                                                                                                                                           |
| [`PARAM_HINTS`](#looks.params.PARAM_HINTS)             | A refused key that deserves more than "unknown parameter".                                                                                                                                          |

### Functions

| [`anything`](#looks.params.anything)(name[, default])                        | A key the effect takes whose shape its compiler owns (a path, a size, a ramp).   |
|---------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------|
| [`as_emitted`](#looks.params.as_emitted)(value)                                | A number as the compilers write it into a filter string, read back.              |
| [`check_params`](#looks.params.check_params)(effect, params, \*[, schemas, ...]) | Refuse an unknown key or a value the effect could not honour.                    |
| [`choice`](#looks.params.choice)(name, options[, default])                 | One of a closed set of strings (an ffmpeg option's enum).                        |
| [`curve`](#looks.params.curve)(name)                                      | At least two `(x, y)` points in 0..1 with x strictly increasing.                 |
| [`flag`](#looks.params.flag)(name[, default])                            | A bool, not truthiness: `"false"` would otherwise be true.                       |
| [`real`](#looks.params.real)(name[, default, low, high, low_open, ...])  | A finite number, optionally bounded.                                             |
| `text`(name[, default])                                                                           |                                                                                  |
| [`vector`](#looks.params.vector)(name, length[, default, low, high, ...])  | `length` finite numbers, each optionally bounded.                                |
| [`whole`](#looks.params.whole)(name[, default, low, high])                | A whole number (`8.0` is fine, `7.9` and `True` are not).                        |
| [`with_defaults`](#looks.params.with_defaults)(effect, params, \*[, schemas])     | The parameters with every declared default filled in; the input is untouched.    |

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

### looks.params.DEPTH_CARRIED_FORMATS *: [frozenset](https://docs.python.org/3/builtins/stdtypes.html#frozenset)* *= frozenset({'0bgr', '0rgb', 'abgr', 'argb', 'bgr0', 'bgr24', 'bgr48be', 'bgr48le', 'bgra', 'bgra64be', 'bgra64le', 'gbrap', 'gbrap16be', 'gbrap16le', 'gbrapf32be', 'gbrapf32le', 'gbrp', 'gbrp10be', 'gbrp10le', 'gbrp12be', 'gbrp12le', 'gbrp16be', 'gbrp16le', 'gbrp9be', 'gbrp9le', 'gbrpf32be', 'gbrpf32le', 'gray', 'gray10be', 'gray10le', 'gray12be', 'gray12le', 'gray16be', 'gray16le', 'gray9be', 'gray9le', 'grayf32be', 'grayf32le', 'nv12', 'nv16', 'nv21', 'nv24', 'p010be', 'p010le', 'p012be', 'p012le', 'p016be', 'p016le', 'p210be', 'p210le', 'p216be', 'p216le', 'p410be', 'p410le', 'p416be', 'p416le', 'rgb0', 'rgb24', 'rgb48be', 'rgb48le', 'rgba', 'rgba64be', 'rgba64le', 'uyvy422', 'x2bgr10le', 'x2rgb10le', 'ya16be', 'ya16le', 'ya8', 'yuv411p', 'yuv420p', 'yuv420p10be', 'yuv420p10le', 'yuv420p12be', 'yuv420p12le', 'yuv420p16be', 'yuv420p16le', 'yuv420p9be', 'yuv420p9le', 'yuv422p', 'yuv422p10be', 'yuv422p10le', 'yuv422p12be', 'yuv422p12le', 'yuv422p16be', 'yuv422p16le', 'yuv440p', 'yuv444p', 'yuv444p10be', 'yuv444p10le', 'yuv444p12be', 'yuv444p12le', 'yuv444p16be', 'yuv444p16le', 'yuv444p9be', 'yuv444p9le', 'yuva420p', 'yuva444p', 'yuva444p16be', 'yuva444p16le', 'yuvj411p', 'yuvj420p', 'yuvj422p', 'yuvj444p', 'yuyv422'})*

Formats whose bit depth survives a step registered with `keeps_depth`
(`EffectRegistry.register`), so `compile_look` may carry the clip’s
format past such a step for the depth checks (issue #52). Measured on 6.1
and 9.0, every keeper on every `CURVES_DEPTH` format: these 18 are
the exceptions, all RAISED to 16 bits by some keeper (`unsharp` takes
every 14-bit format there, `lutyuv` the 10- and 12-bit alpha ones, `geq`
`gbrap12`), and a carried check would refuse what ffmpeg accepts.

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

### looks.params.DFLT_RIPPLE_AMPLITUDE *= 0.017578125*

The ripple warp (issue #49), normalised so one look reads the same at any
size. The values are the 2026-10-27 production’s, judged on a contact sheet
at 1024x576: 18 px of horizontal wander, harmonics of 86 and 33 px, and a
bloom of 0.55 at the peak.
Peak horizontal displacement, as a fraction of the frame’s width.

### looks.params.DFLT_RIPPLE_BLOOM *= 0.55*

Peak weight of the blurred, brightened copy mixed in at the middle.

### looks.params.DFLT_RIPPLE_WAVELENGTHS *= (0.14930555555555555, 0.057291666666666664)*

The two ripple harmonics’ wavelengths, as fractions of the frame’s height.

### looks.params.DFLT_VIGNETTE_ANGLE *= 0.6283185307179586*

Vignette half-angle, radians.

### looks.params.DFLT_WEAVE_AMPLITUDE *= 2*

Gate-weave wander, in pixels either side of centre.

### looks.params.DFLT_WEAVE_FREQUENCY *= (3.44, 2.33)*

Horizontal and vertical wander, Hz. Incommensurate so the path never loops
visibly: the production’s `n*0.9` and `n*0.61` rad/frame, at 24 fps.

### looks.params.EFFECT_PARAMS *: [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Param](#looks.params.Param)]]* *= {'blur': {'sigma': Param(name='sigma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1024]', default=2, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'colorbalance': {'highlights': Param(name='highlights', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers', fits_format=<function Param.<lambda>>), 'midtones': Param(name='midtones', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers', fits_format=<function Param.<lambda>>), 'preserve_lightness': Param(name='preserve_lightness', accepts=<function flag.<locals>.<lambda>>, expects='must be True or False', default=False, kind='flag', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'shadows': Param(name='shadows', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers', fits_format=<function Param.<lambda>>)}, 'contrast': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must not be negative', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'curves': {'all': Param(name='all', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function \_curve_collision>), 'blue': Param(name='blue', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function \_curve_collision>), 'green': Param(name='green', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function \_curve_collision>), 'red': Param(name='red', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function \_curve_collision>)}, 'fill': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'fit': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'flatten': {'planes': Param(name='planes', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 15]', default=7, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>), 'range': Param(name='range', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.05, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'spatial': Param(name='spatial', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 512]', default=60, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'gamma': {'gamma': Param(name='gamma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'gate_weave': {'amplitude': Param(name='amplitude', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, inf]', default=2, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>), 'frequency': Param(name='frequency', accepts=<function vector.<locals>.<lambda>>, expects='must be 2 numbers, each in [0, inf]', default=(3.44, 2.33), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='2 finite numbers', fits_format=<function Param.<lambda>>)}, 'gradient_map': {'contrast': Param(name='contrast', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'interp': Param(name='interp', accepts=<function choice.<locals>.<lambda>>, expects="must be one of ['nearest', 'trilinear', 'tetrahedral', 'pyramid', 'prism']", default='tetrahedral', kind='choice', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'lift': Param(name='lift', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=0.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'size': Param(name='size', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [2, 129]', default=33, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>), 'stops': Param(name='stops', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'title': Param(name='title', accepts=<function text.<locals>.<lambda>>, expects='must be a string', default='looks_gradient_map', kind='text', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'grain': {'seed': Param(name='seed', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 2147483647]', default=0, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>), 'strength': Param(name='strength', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 100]', default=8, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>)}, 'halation': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.5, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'sigma': Param(name='sigma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, 1024], as written to six decimals', default=24.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'threshold': Param(name='threshold', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.78, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'tint': Param(name='tint', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [0, inf]', default=(1.0, 0.35, 0.2), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers', fits_format=<function Param.<lambda>>)}, 'levels': {'black': Param(name='black', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-1, 1]', default=0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'white': Param(name='white', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-1, 1]', default=1, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'lut3d': {'cube': Param(name='cube', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'interp': Param(name='interp', accepts=<function choice.<locals>.<lambda>>, expects="must be one of ['nearest', 'trilinear', 'tetrahedral', 'pyramid', 'prism']", default='tetrahedral', kind='choice', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'motion': {'fps': Param(name='fps', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=<object object>, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'keyframes': Param(name='keyframes', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'output': Param(name='output', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'posterize': {'levels': Param(name='levels', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [2, 256]', default=8, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>)}, 'ripple': {'amplitude': Param(name='amplitude', accepts=<function real.<locals>.<lambda>>, expects='must not be negative', default=0.017578125, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'bloom': Param(name='bloom', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.55, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'duration_s': Param(name='duration_s', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=<object object>, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'start_s': Param(name='start_s', accepts=<function real.<locals>.<lambda>>, expects='must not be negative', default=<object object>, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'wavelengths': Param(name='wavelengths', accepts=<function vector.<locals>.<lambda>>, expects='must be 2 numbers, each in (0, inf]', default=(0.14930555555555555, 0.057291666666666664), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='2 finite numbers', fits_format=<function Param.<lambda>>)}, 'saturation': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'sharpen': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-2, 5]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'stretch': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'vignette': {'angle': Param(name='angle', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, 1.5707963267948966], as written to six decimals', default=0.6283185307179586, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}}*

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

### *class* looks.params.Param(name, accepts, expects, default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One named parameter: how to recognise a valid value, and what omitted means.

`accepts` is the strategy; the constructors below ([`real()`](#looks.params.real),
[`whole()`](#looks.params.whole), [`flag()`](#looks.params.flag), `text()`, [`vector()`](#looks.params.vector), [`curve()`](#looks.params.curve),
[`anything()`](#looks.params.anything)) cover every kind the registered effects need.

#### fits_format(pix_fmt)

A further check against the pixel format the effect receives, when that
is known: why the value does not fit it, or `None` when it does.

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

### looks.params.check_params(effect, params, \*, schemas={'blur': {'sigma': Param(name='sigma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1024]', default=2, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'colorbalance': {'highlights': Param(name='highlights', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers', fits_format=<function Param.<lambda>>), 'midtones': Param(name='midtones', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers', fits_format=<function Param.<lambda>>), 'preserve_lightness': Param(name='preserve_lightness', accepts=<function flag.<locals>.<lambda>>, expects='must be True or False', default=False, kind='flag', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'shadows': Param(name='shadows', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers', fits_format=<function Param.<lambda>>)}, 'contrast': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must not be negative', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'curves': {'all': Param(name='all', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function \_curve_collision>), 'blue': Param(name='blue', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function \_curve_collision>), 'green': Param(name='green', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function \_curve_collision>), 'red': Param(name='red', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function \_curve_collision>)}, 'fill': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'fit': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'flatten': {'planes': Param(name='planes', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 15]', default=7, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>), 'range': Param(name='range', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.05, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'spatial': Param(name='spatial', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 512]', default=60, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'gamma': {'gamma': Param(name='gamma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'gate_weave': {'amplitude': Param(name='amplitude', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, inf]', default=2, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>), 'frequency': Param(name='frequency', accepts=<function vector.<locals>.<lambda>>, expects='must be 2 numbers, each in [0, inf]', default=(3.44, 2.33), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='2 finite numbers', fits_format=<function Param.<lambda>>)}, 'gradient_map': {'contrast': Param(name='contrast', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'interp': Param(name='interp', accepts=<function choice.<locals>.<lambda>>, expects="must be one of ['nearest', 'trilinear', 'tetrahedral', 'pyramid', 'prism']", default='tetrahedral', kind='choice', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'lift': Param(name='lift', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=0.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'size': Param(name='size', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [2, 129]', default=33, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>), 'stops': Param(name='stops', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'title': Param(name='title', accepts=<function text.<locals>.<lambda>>, expects='must be a string', default='looks_gradient_map', kind='text', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'grain': {'seed': Param(name='seed', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 2147483647]', default=0, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>), 'strength': Param(name='strength', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 100]', default=8, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>)}, 'halation': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.5, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'sigma': Param(name='sigma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, 1024], as written to six decimals', default=24.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'threshold': Param(name='threshold', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.78, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'tint': Param(name='tint', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [0, inf]', default=(1.0, 0.35, 0.2), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers', fits_format=<function Param.<lambda>>)}, 'levels': {'black': Param(name='black', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-1, 1]', default=0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'white': Param(name='white', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-1, 1]', default=1, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'lut3d': {'cube': Param(name='cube', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'interp': Param(name='interp', accepts=<function choice.<locals>.<lambda>>, expects="must be one of ['nearest', 'trilinear', 'tetrahedral', 'pyramid', 'prism']", default='tetrahedral', kind='choice', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'motion': {'fps': Param(name='fps', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=<object object>, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'keyframes': Param(name='keyframes', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'output': Param(name='output', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'posterize': {'levels': Param(name='levels', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [2, 256]', default=8, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>)}, 'ripple': {'amplitude': Param(name='amplitude', accepts=<function real.<locals>.<lambda>>, expects='must not be negative', default=0.017578125, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'bloom': Param(name='bloom', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.55, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'duration_s': Param(name='duration_s', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=<object object>, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'start_s': Param(name='start_s', accepts=<function real.<locals>.<lambda>>, expects='must not be negative', default=<object object>, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'wavelengths': Param(name='wavelengths', accepts=<function vector.<locals>.<lambda>>, expects='must be 2 numbers, each in (0, inf]', default=(0.14930555555555555, 0.057291666666666664), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='2 finite numbers', fits_format=<function Param.<lambda>>)}, 'saturation': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'sharpen': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-2, 5]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'stretch': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'vignette': {'angle': Param(name='angle', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, 1.5707963267948966], as written to six decimals', default=0.6283185307179586, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}}, pix_fmt=None)

Refuse an unknown key or a value the effect could not honour.

An effect with no schema is not checked. Only present keys are checked:
an absent one takes its declared default, so a check never has a second
copy of it.

`pix_fmt` is the pixel format the effect receives, or one of the same
bit depth, when the caller knows it; a parameter that depends on it (a
`curves` x-point, issue #33) is checked against it too. `None` checks
only what holds for every format.

```pycon
>>> check_params("curves", {"all": [(0, 0), (0.5, 0.5), (0.501, 1)]})
>>> check_params("curves", {"all": [(0, 0), (0.5, 0.5), (0.501, 1)]}, pix_fmt="rgb24")
Traceback (most recent call last):
...
looks.params.ParamError: curves: all: x-points 0.5 and 0.501 fall in one code value of rgb24 (8-bit), which curves refuses
```

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
is accepted, because the compiler skips an empty channel too. Given the
pixel format the effect receives, x-points are also refused where
`curves` would truncate two of them to one code value of it.

### looks.params.flag(name, default=<object object>)

A bool, not truthiness: `"false"` would otherwise be true.

### looks.params.real(name, default=<object object>, \*, low=None, high=None, low_open=False, emitted=False)

A finite number, optionally bounded. `emitted` bounds it as written.

### looks.params.vector(name, length, default=<object object>, \*, low=None, high=None, low_open=False)

`length` finite numbers, each optionally bounded.

### looks.params.whole(name, default=<object object>, \*, low=None, high=None)

A whole number (`8.0` is fine, `7.9` and `True` are not).

### looks.params.with_defaults(effect, params, \*, schemas={'blur': {'sigma': Param(name='sigma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1024]', default=2, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'colorbalance': {'highlights': Param(name='highlights', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers', fits_format=<function Param.<lambda>>), 'midtones': Param(name='midtones', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers', fits_format=<function Param.<lambda>>), 'preserve_lightness': Param(name='preserve_lightness', accepts=<function flag.<locals>.<lambda>>, expects='must be True or False', default=False, kind='flag', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'shadows': Param(name='shadows', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [-1, 1]', default=(0, 0, 0), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers', fits_format=<function Param.<lambda>>)}, 'contrast': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must not be negative', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'curves': {'all': Param(name='all', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function \_curve_collision>), 'blue': Param(name='blue', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function \_curve_collision>), 'green': Param(name='green', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function \_curve_collision>), 'red': Param(name='red', accepts=<function curve.<locals>.accepts>, expects='must be at least two (x, y) points in 0..1 with x strictly increasing at six decimals', default=<object object>, kind='curve', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function \_curve_collision>)}, 'fill': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'fit': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'flatten': {'planes': Param(name='planes', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 15]', default=7, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>), 'range': Param(name='range', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.05, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'spatial': Param(name='spatial', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 512]', default=60, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'gamma': {'gamma': Param(name='gamma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'gate_weave': {'amplitude': Param(name='amplitude', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, inf]', default=2, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>), 'frequency': Param(name='frequency', accepts=<function vector.<locals>.<lambda>>, expects='must be 2 numbers, each in [0, inf]', default=(3.44, 2.33), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='2 finite numbers', fits_format=<function Param.<lambda>>)}, 'gradient_map': {'contrast': Param(name='contrast', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'interp': Param(name='interp', accepts=<function choice.<locals>.<lambda>>, expects="must be one of ['nearest', 'trilinear', 'tetrahedral', 'pyramid', 'prism']", default='tetrahedral', kind='choice', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'lift': Param(name='lift', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=0.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'size': Param(name='size', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [2, 129]', default=33, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>), 'stops': Param(name='stops', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'title': Param(name='title', accepts=<function text.<locals>.<lambda>>, expects='must be a string', default='looks_gradient_map', kind='text', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'grain': {'seed': Param(name='seed', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 2147483647]', default=0, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>), 'strength': Param(name='strength', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [0, 100]', default=8, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>)}, 'halation': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.5, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'sigma': Param(name='sigma', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, 1024], as written to six decimals', default=24.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'threshold': Param(name='threshold', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.78, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'tint': Param(name='tint', accepts=<function vector.<locals>.<lambda>>, expects='must be 3 numbers, each in [0, inf]', default=(1.0, 0.35, 0.2), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='3 finite numbers', fits_format=<function Param.<lambda>>)}, 'levels': {'black': Param(name='black', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-1, 1]', default=0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'white': Param(name='white', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-1, 1]', default=1, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'lut3d': {'cube': Param(name='cube', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'interp': Param(name='interp', accepts=<function choice.<locals>.<lambda>>, expects="must be one of ['nearest', 'trilinear', 'tetrahedral', 'pyramid', 'prism']", default='tetrahedral', kind='choice', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'motion': {'fps': Param(name='fps', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=<object object>, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'keyframes': Param(name='keyframes', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>), 'output': Param(name='output', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'posterize': {'levels': Param(name='levels', accepts=<function whole.<locals>.<lambda>>, expects='must be a whole number in [2, 256]', default=8, kind='whole', is_type=<function \_is_whole>, type_expects='a whole number', fits_format=<function Param.<lambda>>)}, 'ripple': {'amplitude': Param(name='amplitude', accepts=<function real.<locals>.<lambda>>, expects='must not be negative', default=0.017578125, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'bloom': Param(name='bloom', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [0, 1]', default=0.55, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'duration_s': Param(name='duration_s', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, inf]', default=<object object>, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'start_s': Param(name='start_s', accepts=<function real.<locals>.<lambda>>, expects='must not be negative', default=<object object>, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>), 'wavelengths': Param(name='wavelengths', accepts=<function vector.<locals>.<lambda>>, expects='must be 2 numbers, each in (0, inf]', default=(0.14930555555555555, 0.057291666666666664), kind='vector', is_type=<function vector.<locals>.<lambda>>, type_expects='2 finite numbers', fits_format=<function Param.<lambda>>)}, 'saturation': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-inf, inf]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'sharpen': {'amount': Param(name='amount', accepts=<function real.<locals>.<lambda>>, expects='must be a number in [-2, 5]', default=1.0, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}, 'stretch': {'target': Param(name='target', accepts=<function anything.<locals>.<lambda>>, expects='', default=<object object>, kind='any', is_type=<function Param.<lambda>>, type_expects='', fits_format=<function Param.<lambda>>)}, 'vignette': {'angle': Param(name='angle', accepts=<function real.<locals>.<lambda>>, expects='must be a number in (0, 1.5707963267948966], as written to six decimals', default=0.6283185307179586, kind='real', is_type=<function \_is_real>, type_expects='a finite number', fits_format=<function Param.<lambda>>)}})

The parameters with every declared default filled in; the input is untouched.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)
