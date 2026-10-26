# looks.lut

Gradient-map 3D LUTs: a colour ramp in, an Iridas `.cube` out.

A **gradient map** replaces a pixel’s colour with a colour looked up by its
*lightness* alone. It is the right vehicle when a reference’s hue tracks its
lightness — dark to oxblood, mid to crimson, light to coral — and it is the
wrong one otherwise, which is why the first step is always to measure the
reference rather than assume a filter.

Two properties make it the tool for video specifically:

- **It cannot flicker.** The mapping is per-pixel and stateless, so frame *n*
  and frame *n+1* are transformed by the identical function. That is the
  failure mode of every per-frame palette quantiser and of the non-commercial
  cartoon GANs, and it is bought here for free rather than defended against.
  Measured on the first real look, frame-to-frame change came out at
  0.89–1.12x the *source’s own*, i.e. the chain adds none.
- \*\*It is `lut3d`, which is LGPL.\*\* The obvious alternative for a
  colour-shaping pass is `eq`, and `eq` exists only in a GPL build. So the look
  that ships is also the one that is portable.

Two lessons from building the first real look are baked into the defaults and
the validation here, because both cost real work to learn:

- **Do not end the ramp at black.** A first version crushed 16.2% of pixels to
  L\* 0–5 where the measured reference had 0.3%; the reference’s floor was an
  oxblood at L\* 8.22, never black. Setting the dark anchor to the reference’s
  own measured value took the histogram distance from 46.7 to 32.0 pp. So
  [`gradient_map()`](#looks.lut.gradient_map) warns when a ramp’s darkest stop sits below
  [`SHADOW_FLOOR_WARN_L`](#looks.lut.SHADOW_FLOOR_WARN_L), and the default ramps do not go near it.
- **Accents must survive.** A pure ramp erases every hue distinction, including
  ones the reference keeps. The first look kept warm accents (9.35% of pixels,
  every one warm) through a second, hue-keyed ramp blended in by saturation and
  hue proximity — [`Accent`](#looks.lut.Accent) here.

Everything is stdlib. The full 33³ lattice takes ~22 ms in pure Python, so the
headline capability needs no numpy and lives in the zero-dependency tier. The
resulting file is ~950 KB, which is why a `.cube` is \*\*generated into a cache
keyed by the ramp’s content\*\*, never committed: the ramp is the spec, the file
is a build artifact.

```pycon
>>> ramp = Ramp.from_hex([(0.0, '#1B0610'), (50.0, '#D5254A'), (100.0, '#FEF0DC')])
>>> text = cube_text(ramp, size=2)
>>> text.splitlines()[1]
'LUT_3D_SIZE 2'
>>> len(text.splitlines()) - 5          # header lines are 5
8
```

### Module Attributes

| [`SHADOW_FLOOR_WARN_L`](#looks.lut.SHADOW_FLOOR_WARN_L)   | Lightness of the darkest stop below which [`gradient_map()`](#looks.lut.gradient_map) warns.   |
|------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| [`DFLT_CUBE_SIZE`](#looks.lut.DFLT_CUBE_SIZE)        | Default lattice edge length.                                                                                       |
| [`NEGLIGIBLE_WEIGHT`](#looks.lut.NEGLIGIBLE_WEIGHT)     | Accent weights below this are snapped to exactly 0.0.                                                              |
| [`Rgb`](#looks.lut.Rgb)                   | A colour as three floats in `[0, 1]`, sRGB-encoded (not linear).                                                   |
| [`DFLT_CUBE_TITLE`](#looks.lut.DFLT_CUBE_TITLE)       | The one place the default LUT title is written.                                                                    |
| [`GENERATOR_VERSION`](#looks.lut.GENERATOR_VERSION)     | Bumped when the generation algorithm changes in a way that moves a byte.                                           |

### Functions

| [`cube_key`](#looks.lut.cube_key)(spec, \*[, size, title])                | A content hash of everything that determines the file's bytes.                                                         |
|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------|
| [`cube_text`](#looks.lut.cube_text)(spec, \*[, size, title])               | Render an Iridas `.cube` for `spec`, as text.                                                                          |
| [`gradient_map`](#looks.lut.gradient_map)(ramp, \*[, accent, contrast, lift]) | Build a [`GradientMap`](#looks.lut.GradientMap), warning about a ramp that reaches black.         |
| [`grey_at`](#looks.lut.grey_at)(level)                                   | The sRGB grey whose CIE `L*` is `level` — the inverse of [`lightness()`](#looks.lut.lightness). |
| [`hex_to_rgb`](#looks.lut.hex_to_rgb)(value)                                | `'#RRGGBB'` (or `'RRGGBB'`) to three floats in `[0, 1]`.                                                               |
| [`lightness`](#looks.lut.lightness)(rgb)                                   | CIE `L*` in `[0, 100]` for an sRGB colour.                                                                             |
| [`linear_to_srgb`](#looks.lut.linear_to_srgb)(c)                                | Inverse of [`srgb_to_linear()`](#looks.lut.srgb_to_linear).                                          |
| [`rgb_to_hex`](#looks.lut.rgb_to_hex)(rgb)                                  | Three floats in `[0, 1]` back to `'#RRGGBB'`.                                                                          |
| [`srgb_to_linear`](#looks.lut.srgb_to_linear)(c)                                | The sRGB electro-optical transfer function.                                                                            |
| [`write_cube`](#looks.lut.write_cube)(spec, path, \*[, size, title])        | Write the `.cube` for `spec` to `path` and return it.                                                                  |

### Classes

| [`Accent`](#looks.lut.Accent)(ramp[, hue, hue_width, ...])         | A second ramp for colours the main ramp should not flatten.               |
|----------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| [`GradientMap`](#looks.lut.GradientMap)(ramp[, accent, contrast, lift]) | A ramp, an optional accent, and the tone adjustment applied before both.  |
| [`Ramp`](#looks.lut.Ramp)(stops)                                 | Colours ordered by lightness — the whole specification of a gradient map. |

### Exceptions

| [`LutError`](#looks.lut.LutError)   | A ramp or lattice that cannot produce a usable LUT.   |
|-------------------------------------------------------------|-------------------------------------------------------|

### *class* looks.lut.Accent(ramp, hue=52.0, hue_width=14.0, min_saturation=0.42, saturation_soft=0.3, strength=0.7)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A second ramp for colours the main ramp should not flatten.

A pure gradient map erases every hue distinction. When the reference keeps
one — the first real look kept warm accents, 9.35% of pixels and every one
warm — a second ramp is blended in, weighted by how saturated the source
pixel is and how close its hue sits to [`hue`](#looks.lut.Accent.hue).

#### ramp

The colours this accent maps to, indexed by lightness exactly as
the main ramp is.

* **Type:**
  [`Ramp`](#looks.lut.Ramp)

#### hue

Centre of the hue band to rescue, in degrees.

* **Type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### hue_width

Gaussian sigma of the hue window, in degrees.

* **Type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### min_saturation

Below this saturation, weight is zero — an accent keyed
on hue alone would recolour every near-grey pixel whose hue is
numerically nearby but perceptually meaningless.

* **Type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### saturation_soft

Saturation range over which weight ramps from 0 to 1.

* **Type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### strength

Maximum blend weight, in `[0, 1]`.

* **Type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### weight(rgb)

Blend weight for one source colour, in `[0, strength]`.

### Examples

```pycon
>>> gold = Ramp.from_hex([(0.0, '#2A1206'), (100.0, '#FEF6DF')])
>>> a = Accent(ramp=gold)
>>> round(a.weight((0.95, 0.82, 0.15)), 3)      # a saturated amber
0.695
>>> a.weight((0.5, 0.5, 0.5))                   # grey: no hue to rescue
0.0
>>> a.weight((0.15, 0.30, 0.65))                # blue: outside the band
0.0
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### looks.lut.DFLT_CUBE_SIZE *= 33*

Default lattice edge length. 33 is what Resolve, Premiere and ffmpeg’s
`lut3d` all handle natively and is the de-facto interchange size; 17 is
visibly banded on a smooth ramp, 65 is 8x the file for no visible gain.

### looks.lut.DFLT_CUBE_TITLE *= 'looks_gradient_map'*

The one place the default LUT title is written. It reaches the file’s BYTES
(an Iridas `.cube` opens with `TITLE "..."`), so it must also reach
[`cube_key()`](#looks.lut.cube_key) — see that function’s note on the collision this closes.

### looks.lut.GENERATOR_VERSION *= '2'*

Bumped when the generation algorithm changes in a way that moves a byte.
Without it a cache serves artifacts built by an older generator forever, and
nothing anywhere notices: the spec is unchanged, so the address is unchanged,
so the stale file is a hit. This is the “pin everything that affects output”
rule applied to this package’s own code rather than to a dependency.

### *class* looks.lut.GradientMap(ramp, accent=None, contrast=1.0, lift=0.0)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A ramp, an optional accent, and the tone adjustment applied before both.

#### ramp

The main lightness-indexed ramp.

* **Type:**
  [`Ramp`](#looks.lut.Ramp)

#### accent

An optional second ramp for a hue band the main ramp would
flatten.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Accent`](#looks.lut.Accent)]

#### contrast

Multiplier applied to `L*` around mid-grey before lookup.
`>1` deepens; the first real look used 1.15.

* **Type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### lift

`L*` offset applied after `contrast`. Negative darkens.

* **Type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### Examples

```pycon
>>> gm = GradientMap(ramp=Ramp.from_hex([(0.0, '#1B0610'), (100.0, '#FEF0DC')]))
>>> rgb_to_hex(gm(( 0.0, 0.0, 0.0)))
'#1B0610'
>>> rgb_to_hex(gm(( 1.0, 1.0, 1.0)))
'#FEF0DC'
```

#### to_dict()

A JSON-able form — the thing that is hashed for the cache key.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### *exception* looks.lut.LutError

Bases: [`ValueError`](https://docs.python.org/3/builtins/exceptions.html#ValueError)

A ramp or lattice that cannot produce a usable LUT.

### looks.lut.NEGLIGIBLE_WEIGHT *= 1e-09*

Accent weights below this are snapped to exactly 0.0. The hue window is a
Gaussian, so it never truly reaches zero — a blue pixel against a warm accent
scores ~7e-33, which is float noise rather than a blend. Snapping matters
because `weight() == 0.0` is the predicate [`GradientMap`](#looks.lut.GradientMap) uses to skip
the accent lookup entirely, and a predicate that is never true costs a second
ramp evaluation on every one of 35,937 lattice points.

### *class* looks.lut.Ramp(stops)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Colours ordered by lightness — the whole specification of a gradient map.

#### stops

`(L*, rgb)` pairs, strictly increasing in `L*`, at least two.
`L*` outside a stop’s range clamps to the nearest end.

* **Type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)]], [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### Examples

```pycon
>>> r = Ramp.from_hex([(0.0, '#000000'), (100.0, '#FFFFFF')])
>>> rgb_to_hex(r.at(50.0))
'#808080'
>>> rgb_to_hex(r.at(-10.0))     # clamps
'#000000'
```

#### at(level)

The ramp colour at `L*`, linearly interpolated, clamped at the ends.

### Examples

```pycon
>>> r = Ramp.from_hex([(0.0, '#000000'), (50.0, '#FF0000'), (100.0, '#FFFFFF')])
>>> rgb_to_hex(r.at(25.0))
'#800000'
>>> rgb_to_hex(r.at(75.0))
'#FF8080'
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### *property* darkest *: [float](https://docs.python.org/3/builtins/functions.html#float)*

`L*` of the darkest stop.

### Examples

```pycon
>>> Ramp.from_hex([(8.2, '#2E0C18'), (100.0, '#FEF0DC')]).darkest
8.2
```

#### *classmethod* from_hex(stops)

Build from `(L*, '#RRGGBB')` pairs.

### Examples

```pycon
>>> Ramp.from_hex([(0.0, '#000000'), (100.0, '#FFFFFF')]).stops[1][1]
(1.0, 1.0, 1.0)
```

* **Return type:**
  [`Ramp`](#looks.lut.Ramp)

#### *classmethod* neutral(, stops=32)

A ramp that is a true identity on greys.

\*\*A two-stop black-to-white ramp is NOT an identity, and that surprises
people.\*\* A ramp interpolates its stop colours in *sRGB* while indexing
on *L\**, and those two curves are not the same one: mid-grey sRGB 0.5
is L\* 53.39, so a naive `[(0, black), (100, white)]` ramp returns
sRGB 0.5339 for it. Measured through ffmpeg, that is an \*\*8/255 shift at
every lattice size\*\* — 17, 33 and 65 alike, which is how you know it is
systematic rather than interpolation error, and it peaks in the
midtones rather than the shadows.

This samples the inverse transfer instead, so greys survive. Use it as
the smoke test for any LUT pipeline: an identity that is not an identity
means the transfer or the lattice order is wrong.

### Examples

```pycon
>>> r = Ramp.neutral()
>>> rgb_to_hex(r.at(lightness((0.5, 0.5, 0.5))))
'#808080'
>>> rgb_to_hex(r.at(0.0)), rgb_to_hex(r.at(100.0))
('#000000', '#FFFFFF')
```

* **Return type:**
  [`Ramp`](#looks.lut.Ramp)

#### to_dict()

A JSON-able form, for the cache key and for persisting a Look.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### looks.lut.Rgb

A colour as three floats in `[0, 1]`, sRGB-encoded (not linear).

alias of [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)]

### looks.lut.SHADOW_FLOOR_WARN_L *= 5.0*

Lightness of the darkest stop below which [`gradient_map()`](#looks.lut.gradient_map) warns. The
measured reference’s own floor was L\* 8.22; a ramp reaching L\* 3.6 crushed
16.2% of pixels into the bottom bin where the reference had 0.3%.

### looks.lut.cube_key(spec, , size=33, title='looks_gradient_map')

A content hash of everything that determines the file’s bytes.

A 33-cube is ~950 KB, so a `.cube` is a \*\*build artifact generated into a
cache\*\*, never committed and never carried inside a Look. The ramp is the
spec; this is its address. Two Looks with the same ramp share one file, and
a changed ramp cannot reuse a stale one.

### Examples

```pycon
>>> r = Ramp.from_hex([(0.0, '#000000'), (100.0, '#FFFFFF')])
>>> a, b = cube_key(r), cube_key(r)
>>> a == b and len(a) == 64
True
>>> cube_key(r, size=17) == cube_key(r, size=33)   # size is identity
False
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.lut.cube_text(spec, , size=33, title='looks_gradient_map')

Render an Iridas `.cube` for `spec`, as text.

The lattice order is the format’s own: **red varies fastest**, then green,
then blue. Getting that backwards produces a file that loads without
complaint and swaps the red and blue axes of every colour, which is the
single easiest way to be wrong here.

* **Parameters:**
  * **spec** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`Ramp`](#looks.lut.Ramp), [`GradientMap`](#looks.lut.GradientMap)]) – A [`Ramp`](#looks.lut.Ramp) (used with default tone) or a [`GradientMap`](#looks.lut.GradientMap).
  * **size** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Lattice edge length. 2 is legal and useful for tests.
  * **title** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Written into the file’s `TITLE` line.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### Examples

```pycon
>>> ramp = Ramp.from_hex([(0.0, '#000000'), (100.0, '#FFFFFF')])
>>> text = cube_text(ramp, size=2)
>>> print(text.splitlines()[0])
TITLE "looks_gradient_map"
>>> print(text.splitlines()[1])
LUT_3D_SIZE 2
```

Red fastest: entry 1 is (r=1, g=0, b=0), which for a neutral ramp is a
dark grey rather than a bright one, because red carries only 21% of
luminance.

```pycon
>>> first, second = text.splitlines()[5], text.splitlines()[6]
>>> [round(float(x), 3) for x in first.split()]
[0.0, 0.0, 0.0]
>>> round(float(second.split()[0]), 3)
0.532
```

### looks.lut.gradient_map(ramp, , accent=None, contrast=1.0, lift=0.0)

Build a [`GradientMap`](#looks.lut.GradientMap), warning about a ramp that reaches black.

The warning is the encoded form of a measured mistake: a ramp whose dark end
sat at L\* 3.6 crushed 16.2% of pixels into the bottom bin, where the
reference it was matching had 0.3%. The reference’s own floor was an
oxblood at L\* 8.22 — it had **no true black at all**.

### Examples

```pycon
>>> import warnings
>>> ok = gradient_map(Ramp.from_hex([(8.2, '#2E0C18'), (100.0, '#FEF0DC')]))
>>> ok.ramp.darkest
8.2
```

```pycon
>>> with warnings.catch_warnings(record=True) as w:
...     warnings.simplefilter('always')
...     _ = gradient_map(Ramp.from_hex([(0.0, '#000000'), (100.0, '#FFFFFF')]))
...     print(str(w[0].message)[:43])
ramp reaches L* 0.0, below the L* 5.0 floor
```

* **Return type:**
  [`GradientMap`](#looks.lut.GradientMap)

### looks.lut.grey_at(level)

The sRGB grey whose CIE `L*` is `level` — the inverse of [`lightness()`](#looks.lut.lightness).

### Examples

```pycon
>>> round(grey_at(0.0), 6)
0.0
>>> round(grey_at(100.0), 6)
1.0
>>> round(lightness((grey_at(53.39),) * 3), 2)
53.39
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### looks.lut.hex_to_rgb(value)

`'#RRGGBB'` (or `'RRGGBB'`) to three floats in `[0, 1]`.

### Examples

```pycon
>>> hex_to_rgb('#FFFFFF')
(1.0, 1.0, 1.0)
>>> hex_to_rgb('000000')
(0.0, 0.0, 0.0)
>>> tuple(round(c, 4) for c in hex_to_rgb('#D5254A'))
(0.8353, 0.1451, 0.2902)
>>> hex_to_rgb('#12345')
Traceback (most recent call last):
...
looks.lut.LutError: not a 6-digit hex colour: '#12345'
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)]

### looks.lut.lightness(rgb)

CIE `L*` in `[0, 100]` for an sRGB colour.

This is the axis a gradient map indexes on, and it is deliberately
*perceptual* rather than a naive `(r+g+b)/3` or a coded-Y average: the
whole point of the map is that the output’s lightness ordering matches what
a viewer sees, and the two disagree most on saturated colour, which is
exactly where an extreme look lives.

### Examples

```pycon
>>> round(lightness((0.0, 0.0, 0.0)), 4)
0.0
>>> round(lightness((1.0, 1.0, 1.0)), 4)
100.0
>>> round(lightness((0.5, 0.5, 0.5)), 2)
53.39
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### looks.lut.linear_to_srgb(c)

Inverse of [`srgb_to_linear()`](#looks.lut.srgb_to_linear).

### Examples

```pycon
>>> round(linear_to_srgb(srgb_to_linear(0.37)), 6)
0.37
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### looks.lut.rgb_to_hex(rgb)

Three floats in `[0, 1]` back to `'#RRGGBB'`.

### Examples

```pycon
>>> rgb_to_hex((1.0, 1.0, 1.0))
'#FFFFFF'
>>> rgb_to_hex((0.8353, 0.1451, 0.2902))
'#D5254A'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.lut.srgb_to_linear(c)

The sRGB electro-optical transfer function.

### Examples

```pycon
>>> srgb_to_linear(0.0)
0.0
>>> srgb_to_linear(1.0)
1.0
>>> round(srgb_to_linear(0.5), 4)
0.214
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### looks.lut.write_cube(spec, path, , size=33, title='looks_gradient_map')

Write the `.cube` for `spec` to `path` and return it.

Creates parent directories. Writing is not conditional on the file’s
absence — the caller owns the cache policy, and this owns the bytes.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)
