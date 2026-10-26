# looks.geometry

Where a source frame lands inside a target frame. Pure arithmetic.

No I/O, no media library, no ffmpeg, no numpy. Every function here is total:
give it two sizes and a mode and it answers, with no file open and nothing
decoded. That is what lets one answer drive an ffmpeg filter chain, a moviepy
composite, a CSS `object-fit` preview, or a cost estimate — and it is why the
geometry tier can be a *spec* rather than a call.

**The rounding rule is part of the answer, not an implementation detail.**
`mixing` and moviepy truncate; ffmpeg’s `force_original_aspect_ratio` rounds.
On real inputs they disagree: 1920x1080 into 1080x1920 gives `1080/(16/9) =
607.5`, which truncates to **607** and rounds to **608**. One pixel row, and a
total black-to-white difference at the seam. A spec whose rendered result
depends on which backend read it is not a spec, so the rule travels inside the
[`Placement`](#looks.geometry.Placement).

The three modes are the ones `mixing` already had, and they answer three
different questions:

- `stretch` — fill the target exactly, distorting. The only mode that changes
  the aspect ratio.
- `fit` — the whole source is visible; the target is padded. Nothing is lost.
- `fill` — the target is covered; the source is cropped. Nothing is padded.

`mixing`’s fourth, `social`, is not a fourth mode: it is `fit` with a
blurred, dimmed copy of the source behind it instead of a solid colour. That is
a [`Backdrop`](#looks.geometry.Backdrop), and separating the two is what lets a caller put a blurred
backdrop behind a `fill` or a solid colour behind a `social` layout without
a fifth mode appearing.

```pycon
>>> placement(Size(1920, 1080), Size(1080, 1920), mode="fit").scale
Size(width=1080, height=607)
>>> placement(Size(1920, 1080), Size(1080, 1920), mode="fit",
...           rounding="exact_half_away").scale
Size(width=1080, height=608)
```

### Module Attributes

| [`DFLT_ROUNDING`](#looks.geometry.DFLT_ROUNDING)            | How a non-integer size is resolved.                                                                                                  |
|---------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| [`DFLT_BACKDROP_BLUR_SIGMA`](#looks.geometry.DFLT_BACKDROP_BLUR_SIGMA) | Backdrop defaults, transcribed from `mixing.resize_to_dimensions`'s `method="social"` branch so the extracted version reproduces it. |
| [`SOCIAL_SIZES`](#looks.geometry.SOCIAL_SIZES)             | Named target sizes.                                                                                                                  |
| [`Backdrop`](#looks.geometry.Backdrop)                 | What fills the part of the target the placed frame does not cover.                                                                   |

### Functions

| [`center_box`](#looks.geometry.center_box)(inner, outer)                           | `inner` centred in `outer`, halving with the floor `mixing` used.                    |
|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|
| [`ffmpeg_chain`](#looks.geometry.ffmpeg_chain)(placement, \*[, backdrop])            | The resolved `scale,crop,pad` chain for one placement.                               |
| [`placement`](#looks.geometry.placement)(source, target, \*[, mode, rounding])    | The full geometric answer for one clip.                                              |
| [`reframe`](#looks.geometry.reframe)(source, target, \*[, mode, backdrop, ...]) | [`placement()`](#looks.geometry.placement) plus a backdrop.        |
| [`scaled_size`](#looks.geometry.scaled_size)(source, target, \*[, mode, rounding])  | The size the source is scaled to, before any crop or pad.                            |
| [`snap_even`](#looks.geometry.snap_even)(size)                                    | Both axes rounded **down** to even — the yuv420p requirement.                        |
| [`social_size`](#looks.geometry.social_size)(name)                                  | Resolve a [`SOCIAL_SIZES`](#looks.geometry.SOCIAL_SIZES) preset name. |

### Classes

| [`Blurred`](#looks.geometry.Blurred)([sigma, dim])                         | A blurred, dimmed copy of the source, scaled to cover — the "social" look.   |
|------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------|
| [`Box`](#looks.geometry.Box)(x, y, width, height)                      | An axis-aligned pixel box, top-left origin, y downwards.                     |
| [`Placement`](#looks.geometry.Placement)(source, target, scale[, crop, ...]) | Scale the source to `scale`, take `crop` out, put it at `offset`.            |
| [`Reframe`](#looks.geometry.Reframe)(placement[, backdrop])                | A placement plus what fills the part of the target it does not cover.        |
| [`Size`](#looks.geometry.Size)(width, height)                           | A pixel size.                                                                |
| [`Solid`](#looks.geometry.Solid)([rgb])                                  | A flat colour behind the placed frame.                                       |

### Exceptions

| [`GeometryError`](#looks.geometry.GeometryError)   | A size or mode that cannot produce a placement.   |
|------------------------------------------------------------------|---------------------------------------------------|

### looks.geometry.Backdrop

What fills the part of the target the placed frame does not cover.

alias of [`Solid`](#looks.geometry.Solid) | [`Blurred`](#looks.geometry.Blurred)

### *class* looks.geometry.Blurred(sigma=15.0, dim=0.7)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A blurred, dimmed copy of the source, scaled to cover — the “social” look.

This is `mixing`’s `method="social"`, separated from the fit mode so that
the two compose. Its defaults reproduce that branch.

### Examples

```pycon
>>> Blurred().sigma, Blurred().dim
(15.0, 0.7)
```

### *class* looks.geometry.Box(x, y, width, height)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

An axis-aligned pixel box, top-left origin, y downwards.

Deliberately **not** `burns.Rect`: that one is normalised to `[0, 1]`
over a source image and interpolates over time. This one is integer pixels
in one frame and does not move. The distinction is the same one that keeps
the two packages apart — `burns` owns *authored* geometry over time,
`looks` owns geometry *derived* from a pair of sizes.

### Examples

```pycon
>>> Box(240, 0, 1439, 1080).size
Size(width=1439, height=1080)
```

### looks.geometry.DFLT_BACKDROP_BLUR_SIGMA *= 15.0*

Backdrop defaults, transcribed from `mixing.resize_to_dimensions`’s
`method="social"` branch so the extracted version reproduces it.

### looks.geometry.DFLT_ROUNDING *: [Literal](https://docs.python.org/3/library/typing.html#typing.Literal)['exact_floor', 'exact_half_away']* *= 'exact_floor'*

How a non-integer size is resolved. \*\*Both names carry the arithmetic domain,
not just the tie-break\*\*, because the ambiguous word is what produced a bug.

`"exact_floor"` reproduces `mixing.resize_to_dimensions`: the floor of an
exact rational. `"exact_half_away"` reproduces ffmpeg’s
`force_original_aspect_ratio`, which is `av_rescale` with
`AV_ROUND_NEAR_INF` — half **away from zero**, on exact int64 rationals.

Both are computed with integer arithmetic. An earlier version used
`int(round(value))` on a float, which is Python’s half-to-**even** — a
different rule that disagrees with ffmpeg on **6 of 4000** ordinary
source/target pairs, and the one doctest that had been chosen
(1920x1080 -> 1080x1920, 607 against 608) is precisely a case where the
divergence is invisible because 608 happens to be even. Float truncation had
the same latent problem for `floor`: a `Placement` that renders differently
depending on who reads it is exactly what carrying the rule was meant to
prevent.

### *exception* looks.geometry.GeometryError

Bases: [`ValueError`](https://docs.python.org/3/builtins/exceptions.html#ValueError)

A size or mode that cannot produce a placement.

### *class* looks.geometry.Placement(source, target, scale, crop=None, offset=None, rounding='exact_floor')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Scale the source to `scale`, take `crop` out, put it at `offset`.

`crop` and `offset` are `None` when that pass is a no-op, so a
backend emits nothing for it rather than an identity filter. That matters
for more than tidiness: an identity `scale` still resamples, and a chain
that resamples when it did not need to loses detail for free.

`rounding` is carried, not assumed — see the module docstring.

### Examples

```pycon
>>> p = placement(Size(641, 481), Size(1920, 1080), mode="fill")
>>> p.scale
Size(width=1920, height=1440)
>>> p.crop
Box(x=0, y=180, width=1920, height=1080)
>>> p.offset is None
True
```

#### *property* resamples *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Whether this placement actually changes the pixel grid.

### Examples

```pycon
>>> placement(Size(64, 36), Size(64, 36)).resamples
False
>>> placement(Size(64, 36), Size(128, 72)).resamples
True
```

### *class* looks.geometry.Reframe(placement, backdrop=Solid())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A placement plus what fills the part of the target it does not cover.

This is the shape a `Look` stores: geometry is a spec, and a spec has to
say what the empty region contains, or two backends will disagree about it.

### Examples

```pycon
>>> r = reframe(Size(480, 850), Size(1280, 720))
>>> r.placement.offset, r.backdrop
((437, 0), Solid(rgb=(0, 0, 0)))
>>> reframe(Size(480, 850), Size(1280, 720), backdrop=Blurred()).backdrop
Blurred(sigma=15.0, dim=0.7)
```

### looks.geometry.SOCIAL_SIZES *: [dict](https://docs.python.org/3/builtins/stdtypes.html#dict)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[int](https://docs.python.org/3/builtins/functions.html#int), [int](https://docs.python.org/3/builtins/functions.html#int)]]* *= {'shorts': (1080, 1920), 'square': (1080, 1080), 'story': (1080, 1920), 'tiktok': (1080, 1920), 'youtube': (1920, 1080)}*

Named target sizes. Kept because callers ask for “a YouTube Short”, not for
1080x1920 — but see [`social_size()`](#looks.geometry.social_size): these are a *convenience over*
[`Size`](#looks.geometry.Size), never a parallel vocabulary. Nothing in this module takes a
preset name; they resolve to a `Size` at the boundary.

### *class* looks.geometry.Size(width, height)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A pixel size. `aspect` is width/height, never the other way round.

### Examples

```pycon
>>> Size(1920, 1080).aspect
1.7777777777777777
>>> Size(0, 10)
Traceback (most recent call last):
...
looks.geometry.GeometryError: a Size must be positive, got 0x10
```

### *class* looks.geometry.Solid(rgb=(0, 0, 0))

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A flat colour behind the placed frame.

### Examples

```pycon
>>> Solid().rgb
(0, 0, 0)
```

### looks.geometry.center_box(inner, outer)

`inner` centred in `outer`, halving with the floor `mixing` used.

### Examples

```pycon
>>> center_box(Size(1439, 1080), Size(1920, 1080))
Box(x=240, y=0, width=1439, height=1080)
```

An odd leftover goes to the right/bottom, because the offset floors:

```pycon
>>> center_box(Size(3, 1), Size(4, 1))
Box(x=0, y=0, width=3, height=1)
```

* **Return type:**
  [`Box`](#looks.geometry.Box)

### looks.geometry.ffmpeg_chain(placement, , backdrop=None)

The resolved `scale,crop,pad` chain for one placement.

**Resolved, not deferred.** ffmpeg can express fit and fill without knowing
the source size, via `scale=W:H:force_original_aspect_ratio=decrease`, and
that form is nearly identical — but *nearly* is the problem: it rounds where
this floors, so 1920x1080 into 1080x1920 differs by one row and the seam
goes black-to-white. More fundamentally, a placement that does not know its
source size cannot be inspected or diffed, which is the premise of the whole
package. Resolve against the clip, then emit.

Only a solid backdrop is emitted here; a [`Blurred`](#looks.geometry.Blurred) backdrop needs a
second copy of the input and therefore a two-branch graph, which is the
compiler’s business rather than this function’s.

### Examples

```pycon
>>> p = placement(Size(480, 850), Size(1280, 720))
>>> ffmpeg_chain(p)
'scale=406:720,pad=1280:720:437:0:color=0x000000'
```

Filling crops instead of padding:

```pycon
>>> p = placement(Size(480, 850), Size(1280, 720), mode="fill")
>>> ffmpeg_chain(p)
'scale=1280:2266,crop=1280:720:0:773'
```

A no-op placement emits a no-op chain, not an identity scale:

```pycon
>>> ffmpeg_chain(placement(Size(1280, 720), Size(1280, 720)))
''
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.geometry.placement(source, target, , mode='fit', rounding='exact_floor')

The full geometric answer for one clip.

`fit` pads and never crops; `fill` crops and never pads; `stretch`
does neither.

### Examples

A portrait source into a landscape frame, fitted — padded left/right:

```pycon
>>> p = placement(Size(480, 850), Size(1280, 720))
>>> p.scale, p.crop, p.offset
(Size(width=406, height=720), None, (437, 0))
```

The same pair, filled — cropped top/bottom, nothing padded:

```pycon
>>> p = placement(Size(480, 850), Size(1280, 720), mode="fill")
>>> p.scale, p.crop, p.offset
(Size(width=1280, height=2266), Box(x=0, y=773, width=1280, height=720), None)
```

Same size in and out: nothing happens at all.

```pycon
>>> p = placement(Size(1280, 720), Size(1280, 720))
>>> p.scale, p.crop, p.offset, p.resamples
(Size(width=1280, height=720), None, None, False)
```

* **Return type:**
  [`Placement`](#looks.geometry.Placement)

### looks.geometry.reframe(source, target, , mode='fit', backdrop=None, rounding='exact_floor')

[`placement()`](#looks.geometry.placement) plus a backdrop.

* **Return type:**
  [`Reframe`](#looks.geometry.Reframe)

### looks.geometry.scaled_size(source, target, , mode='fit', rounding='exact_floor')

The size the source is scaled to, before any crop or pad.

### Examples

```pycon
>>> scaled_size(Size(1920, 1080), Size(1080, 1920), mode="fit")
Size(width=1080, height=607)
```

The rounding rule is visible right here, on an ordinary input — this is
the 607-versus-608 disagreement, not a contrived case:

```pycon
>>> scaled_size(Size(1920, 1080), Size(1080, 1920), mode="fit",
...             rounding="exact_half_away")
Size(width=1080, height=608)
```

`fill` covers instead of fitting, so it goes the other way:

```pycon
>>> scaled_size(Size(1920, 1080), Size(1080, 1920), mode="fill")
Size(width=3413, height=1920)
```

`stretch` is the target, by definition:

```pycon
>>> scaled_size(Size(1920, 1080), Size(1080, 1920), mode="stretch")
Size(width=1080, height=1920)
```

* **Return type:**
  [`Size`](#looks.geometry.Size)

### looks.geometry.snap_even(size)

Both axes rounded **down** to even — the yuv420p requirement.

H.264 in yuv420p subsamples chroma 2x2, so an odd dimension is not
encodable. Down rather than up, so the result never exceeds a target the
caller asked for.

### Examples

```pycon
>>> snap_even(Size(1439, 1081))
Size(width=1438, height=1080)
>>> snap_even(Size(1920, 1080))
Size(width=1920, height=1080)
```

* **Return type:**
  [`Size`](#looks.geometry.Size)

### looks.geometry.social_size(name)

Resolve a [`SOCIAL_SIZES`](#looks.geometry.SOCIAL_SIZES) preset name.

A convenience over [`Size`](#looks.geometry.Size), never a parallel vocabulary — nothing else
in this module accepts a preset name, so a preset cannot acquire behaviour
of its own.

### Examples

```pycon
>>> social_size('shorts')
Size(width=1080, height=1920)
>>> social_size('myspace')
Traceback (most recent call last):
...
looks.geometry.GeometryError: unknown size preset 'myspace'; known: ...
```

* **Return type:**
  [`Size`](#looks.geometry.Size)
