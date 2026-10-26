# looks.motion

A camera path, compiled to an ffmpeg fragment — the compile half of RULE G.

RULE G splits authored geometry from its compilation. `burns` owns the
**authored** side: a `BurnsPath` with keyframes and easing, which exists
because someone chose it as the shot. `looks` owns the **compiled** side,
because a moving window expressed as `crop=x='iw*(...)'` is ffmpeg vocabulary
and nothing else — the same reason `looks` owns every other filter string.

So this module takes keyframes and returns a string. It does not ease, does not
sample a path, does not decide where a camera should go, and \*\*never imports
burns\*\* — the dependency points `burns -> looks`, which is legal because
`looks` is stdlib-only, and the reverse stays forbidden because `burns`
pulls `moviepy`, which pulls a GPL ffmpeg binary. A window here is anything
with `.x`/`.y`/`.w`/`.h` in burns’ normalised, top-left, window-fraction
convention. Adopting a third rect convention is the mistake `muvid.CropWindow`’s
docstring already exists to prevent.

Easing lives on the far side of this boundary on purpose. An eased path is
sampled by its owner into as many keyframes as it needs, and what arrives here
is interpolated **linearly** between them. That is not a limitation being
tolerated; it is what makes the seam a seam: `looks` never has to know what
`ease_in_out_cubic` means, and `burns` never has to know what `in_time` is.

### Which filter, and why it is not a matter of taste

Measured on ffmpeg 8.1, 2026-09-02 — the full transcript is
`docs/research/00f_motion_filters_evidence.md`.

The third row is the one that decides the module. `crop`’s `w`/`h` do not
merely evaluate once — `t` is not in scope for them and the filter \*\*refuses
to configure\*\*, which is structural: a filter link has one fixed frame size. So
a Ken Burns path, which is a zoom by definition, is not compilable to `crop`
at all.

This **overturns a recorded fleet fact.** `muvid._crop_filter`’s docstring —
propagated by two of this package’s own research notes into a warning aimed at
the `burns` owner — says  *“Not zoompan: its expression vocabulary has no t at
all, and it duplicates frames on video input.”* Both premises are true and the
conclusion is wrong: `t` is undefined but `in_time` is not, and the
duplication is the default `d` rather than a property of the filter (`d=1`
gives exactly 1:1, measured 20 frames from 20). `muvid`’s own code is correct
— it compiles a *pan*, which is the case where `crop` is right and simpler.

Three `zoompan` traps are compiled away here so that no caller has to
remember them:

- its `x`/`y` are in **original input pixels**, not zoomed ones (60.5 dB
  against the reference versus 6.3 dB for the other reading);
- its `fps` **silently retimes** — at `fps=25` on a 10 fps source the frame
  count is unchanged and the clip is 60% shorter, so it is required here, never
  defaulted;
- its `zoom` is one scalar, so the visible window is always geometrically
  similar to the source frame, and a window that is not is refused rather than
  distorted on one axis.

### Module Attributes

| [`EPSILON`](#looks.motion.EPSILON)             | Two normalised fractions are the same window edge within this.                                                                                                                                            |
|----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`PRECISION`](#looks.motion.PRECISION)           | How many decimals of a normalised fraction reach the filter string.                                                                                                                                       |
| [`MAX_ZOOM`](#looks.motion.MAX_ZOOM)            | against a reference built with `crop``+``scale`, z=10 scores 54.4 dB and z=12 scores 13.2 dB — the second is not a worse rendering of the window asked for, it is a correct rendering of a different one. |
| [`MIN_WINDOW_FRACTION`](#looks.motion.MIN_WINDOW_FRACTION) | The consequence of [`MAX_ZOOM`](#looks.motion.MAX_ZOOM), in the units this module speaks.                                                                                            |
| [`ASPECT_TOLERANCE`](#looks.motion.ASPECT_TOLERANCE)    | How far two windows' aspect ratios may differ, relatively, and still count as the same shape.                                                                                                             |
| [`TIMEBASE_RESET`](#looks.motion.TIMEBASE_RESET)      | Prepended to a moving `crop` and never to a static one.                                                                                                                                                   |

### Functions

| [`compile_motion`](#looks.motion.compile_motion)(keyframes, \*[, output, fps, ...])   | A camera path to an ffmpeg fragment, filter chosen by what the path does.   |
|------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| [`crop_fragment`](#looks.motion.crop_fragment)(keyframes)                            | A path of constant window size, compiled to `crop`.                         |
| [`is_source_shaped`](#looks.motion.is_source_shaped)(keyframes)                         | Is every window geometrically similar to the whole frame?                   |
| [`is_static`](#looks.motion.is_static)(keyframes)                                | Does the window never move? Then no clock is needed at all.                 |
| [`ramp`](#looks.motion.ramp)(points, clock)                                 | Piecewise-linear interpolation of `points` as one ffmpeg expression.        |
| [`reframe`](#looks.motion.reframe)(keyframes, \*[, aspect_tolerance])          | Split a path into a static reframing crop and a path relative to it.        |
| [`zoompan_fragment`](#looks.motion.zoompan_fragment)(keyframes, \*, output, fps)        | A path whose window size varies, compiled to `zoompan`.                     |
| [`zooms`](#looks.motion.zooms)(keyframes)                                    | Does the window's SIZE change? That is the question that picks a filter.    |

### Classes

| [`Keyframe`](#looks.motion.Keyframe)(t, window)            | A window, at a time in seconds from the start of the clip.                                                       |
|---------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| [`Window`](#looks.motion.Window)(x, y, w, h)             | A concrete [`WindowLike`](#looks.motion.WindowLike), for callers who do not already have one. |
| [`WindowLike`](#looks.motion.WindowLike)(\*args, \*\*kwargs) | Burns' convention: normalised, top-left origin, window fractions.                                                |

### Exceptions

| [`MotionError`](#looks.motion.MotionError)   | A path that cannot be compiled, or that would compile to a lie.   |
|----------------------------------------------------------------|-------------------------------------------------------------------|

### looks.motion.ASPECT_TOLERANCE *= 1e-06*

How far two windows’ aspect ratios may differ, relatively, and still count as
the same shape. Float noise only — this is NOT a place to absorb quantisation.
A caller reading windows out of integer pixel boxes (burns’ `sample_box` does)
gets ratios spread by up to a pixel’s worth, and the fix is for that caller to
normalise the aspect it intended, not for this to look the other way: widening
it here would silently render a shape nobody asked for.

### looks.motion.EPSILON *= 1e-09*

Two normalised fractions are the same window edge within this. Tighter than
any authoring tool’s precision and looser than float noise from easing
arithmetic, which is where these numbers come from.

### *class* looks.motion.Keyframe(t, window)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A window, at a time in seconds from the start of the clip.

```pycon
>>> Keyframe(0.0, Window.full())
Keyframe(t=0.0, window=Window(x=0.0, y=0.0, w=1.0, h=1.0))
```

### looks.motion.MAX_ZOOM *= 10.0*

against a
reference built with `crop``+``scale`, z=10 scores 54.4 dB and z=12 scores
13.2 dB — the second is not a worse rendering of the window asked for, it is
a correct rendering of a different one. So the smallest window `zoompan`
can show is 1/10 of the frame, and asking for less is refused here rather
than honoured as something else.

* **Type:**
  `zoompan` clamps its `zoom` here, **silently**. Measured

### looks.motion.MIN_WINDOW_FRACTION *= 0.1*

The consequence of [`MAX_ZOOM`](#looks.motion.MAX_ZOOM), in the units this module speaks.

### *exception* looks.motion.MotionError

Bases: [`GeometryError`](looks.geometry.html.md#looks.geometry.GeometryError)

A path that cannot be compiled, or that would compile to a lie.

### looks.motion.PRECISION *= 6*

How many decimals of a normalised fraction reach the filter string. At 1e-6
of a 3840-pixel frame that is 0.004 px — far below the integer rounding both
filters do anyway, and it keeps the emitted string readable.

### looks.motion.TIMEBASE_RESET *= 'setpts=PTS-STARTPTS'*

Prepended to a moving `crop` and never to a static one. `t` must start at
0 for a ramp to mean anything; adding it unconditionally would change a path
that already works. Inherited verbatim, reason included, from
`muvid.footage.assemble._crop_filter`.

### *class* looks.motion.Window(x, y, w, h)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A concrete [`WindowLike`](#looks.motion.WindowLike), for callers who do not already have one.

```pycon
>>> Window(0.25, 0.25, 0.5, 0.5)
Window(x=0.25, y=0.25, w=0.5, h=0.5)
```

The whole frame is the identity window:

```pycon
>>> Window.full()
Window(x=0.0, y=0.0, w=1.0, h=1.0)
```

### *class* looks.motion.WindowLike(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Burns’ convention: normalised, top-left origin, window fractions.

Structural on purpose — `burns.Rect` satisfies it without `looks`
importing `burns`, and so does anything else a caller already has.

### looks.motion.compile_motion(keyframes, , output=None, fps=None, aspect_tolerance=1e-06)

A camera path to an ffmpeg fragment, filter chosen by what the path does.

The one entry point. Which filter is not a caller’s decision, because it is
not a matter of taste — it follows from whether the window’s size varies,
and getting it wrong is a configure-time error or a silent retime.

A static window needs no clock:

```pycon
>>> compile_motion([Keyframe(0, Window(0, 0, 0.5, 0.5))])
"crop=w='iw*0.5':h='ih*0.5':x='iw*0':y='ih*0'"
```

A pan compiles to `crop` and needs nothing else:

```pycon
>>> print(compile_motion([
...     Keyframe(0.0, Window(0.0, 0.0, 0.5, 1.0)),
...     Keyframe(2.0, Window(0.5, 0.0, 0.5, 1.0)),
... ]))
setpts=PTS-STARTPTS,crop=w='iw*0.5':h='ih*1':x='iw*(0+(0.5)*min(max((t-0)/2,0),1))':y='ih*0'
```

A pan given a delivery size is scaled to it, because `crop` otherwise
emits the window’s own odd-numbered pixel size and the encoder refuses:

```pycon
>>> compile_motion(
...     [Keyframe(0.0, Window(0.0, 0.0, 0.5, 1.0)),
...      Keyframe(2.0, Window(0.5, 0.0, 0.5, 1.0))],
...     output=Size(1280, 720),
... ).endswith(",scale=1280:720")
True
```

A zoom compiles to `zoompan`, and must be told the delivery size and the
source’s rate:

```pycon
>>> fragment = compile_motion(
...     [Keyframe(0, Window.full()), Keyframe(3, Window(0.1, 0.1, 0.8, 0.8))],
...     output=Size(1280, 720), fps=25,
... )
>>> fragment.startswith("zoompan=d=1:s=1280x720:fps=25:")
True
```

A zooming path whose windows are not the source’s shape — the Ken Burns
case, a 4:3 still delivered at 16:9 — is **reframed** rather than refused:
a static crop to the windows’ aspect is emitted first, and the motion runs
inside it. See [`reframe()`](#looks.motion.reframe).

```pycon
>>> compile_motion(
...     [Keyframe(0.0, Window(0.0, 0.2, 1.0, 0.5)),
...      Keyframe(2.0, Window(0.1, 0.3, 0.8, 0.4))],
...     output=Size(1920, 1080), fps=25,
... ).startswith("crop=")
True
```

* **Raises:**
  [**MotionError**](#looks.motion.MotionError) – If a zoom is asked for without `output` and `fps`.
      They are not defaultable: `zoompan`’s own `fps` default retimes
      the clip, and there is no honest guess for a delivery size.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.motion.crop_fragment(keyframes)

A path of constant window size, compiled to `crop`.

Normalised fractions become pixels only once the source dimensions are
known, and the only thing that knows them is ffmpeg — hence `iw`/`ih`
rather than arithmetic here. That is what makes the fragment
resolution-independent and input-index-free, which is what lets a consumer
splice it into a filter string it already owns.

```pycon
>>> crop_fragment([Keyframe(0, Window(0.25, 0.1, 0.5, 0.5))])
"crop=w='iw*0.5':h='ih*0.5':x='iw*0.25':y='ih*0.1'"
```

A moving window gets its clock reset, and only then:

```pycon
>>> print(crop_fragment([
...     Keyframe(0, Window(0, 0, 0.5, 1)),
...     Keyframe(2, Window(0.5, 0, 0.5, 1)),
... ]))
setpts=PTS-STARTPTS,crop=w='iw*0.5':h='ih*1':x='iw*(0+(0.5)*min(max((t-0)/2,0),1))':y='ih*0'
```

* **Raises:**
  [**MotionError**](#looks.motion.MotionError) – If the window’s size varies. `crop`’s `w`/`h` do not
      accept `t` — the filter refuses to configure — so this is not a
      missing feature that could be added later.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.motion.is_source_shaped(keyframes)

Is every window geometrically similar to the whole frame?

The condition `zoompan` needs, in the units this module speaks. A window’s
pixel aspect is `(w*iw)/(h*ih)` and the source’s is `iw/ih`, so the two
are similar exactly when the normalised `w` and `h` are equal — which is
why this reads as a suspiciously simple comparison.

```pycon
>>> is_source_shaped([Keyframe(0, Window(0.1, 0.1, 0.5, 0.5))])
True
>>> is_source_shaped([Keyframe(0, Window(0, 0, 1.0, 0.5))])
False
```

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### looks.motion.is_static(keyframes)

Does the window never move? Then no clock is needed at all.

```pycon
>>> a, b = Window(0, 0, 0.5, 0.5), Window(0, 0, 0.5, 0.5)
>>> is_static([Keyframe(0, a), Keyframe(2, b)])
True
>>> is_static([Keyframe(0, a), Keyframe(2, Window(0.5, 0, 0.5, 0.5))])
False
```

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### looks.motion.ramp(points, clock)

Piecewise-linear interpolation of `points` as one ffmpeg expression.

A sum of clamped ramps rather than nested `if()`: it is exact at every
knot, linear between them, and — the property that matters — \*\*flat outside
the path on both sides\*\*, because every term saturates. That is the clamping
`muvid._crop_filter` does at two keyframes, generalised to N without
growing a branch.

```pycon
>>> ramp([(0.0, 10.0)], "t")
'10'
>>> ramp([(0.0, 0.0), (2.0, 1.0)], "t")
'(0+(1)*min(max((t-0)/2,0),1))'
```

Held before the first keyframe and after the last, which is what stops a
clip that outlives its path from drifting off the end:

```pycon
>>> ramp([(1.0, 5.0), (3.0, 9.0)], "in_time")
'(5+(4)*min(max((in_time-1)/2,0),1))'
```

A segment that does not move contributes `0 * something`, so it is not
emitted; an axis that never moves collapses to the constant it is. This is
not cosmetic — it is the difference between ffmpeg evaluating an expression
per frame and reading a number once:

```pycon
>>> ramp([(0.0, 0.4), (2.0, 0.4), (5.0, 0.9)], "t")
'(0.4+(0.5)*min(max((t-2)/3,0),1))'
>>> ramp([(0.0, 0.25), (2.0, 0.25)], "t")
'0.25'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.motion.reframe(keyframes, , aspect_tolerance=1e-06)

Split a path into a static reframing crop and a path relative to it.

`zoompan`’s `zoom` is one scalar, so it can only ever show a window
similar to its input. A Ken Burns path over a 4:3 still delivered at 16:9 is
therefore not directly compilable — and that is the headline case, not an
edge one.

The fix is derived geometry, which is why it lives here rather than with
whoever authored the path: nobody *chooses* the reframe, it falls out of the
mismatch between the source’s shape and the delivery’s. Crop the source once
to the windows’ own aspect, then move within that — and the windows, being
that aspect, are similar to it.

The crop is the **bounding box of every window**, grown on one axis to reach
the required aspect and nudged to stay inside the frame. Bounding box rather
than a centred crop because a centred one can exclude a window the path
actually visits, which would silently reframe the shot.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Window`](#looks.motion.Window)], [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Keyframe`](#looks.motion.Keyframe), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]]
* **Returns:**
  `(None, keyframes)` when no reframe is needed — so a path that already
  worked compiles to the identical fragment it did before. Otherwise the
  crop and the path re-expressed against it.

A path already shaped like its source needs nothing:

```pycon
>>> reframe([Keyframe(0, Window(0.25, 0.25, 0.5, 0.5))])[0] is None
True
```

A 16:9-shaped window over a square-normalised frame is reframed, and the
re-expressed window comes out square — which is what `zoompan` requires:

```pycon
>>> crop, path = reframe([Keyframe(0, Window(0.0, 0.25, 1.0, 0.5))])
>>> crop
Window(x=0.0, y=0.25, w=1.0, h=0.5)
>>> path[0].window
Window(x=0.0, y=0.0, w=1.0, h=1.0)
```

* **Raises:**
  [**MotionError**](#looks.motion.MotionError) – If the windows are not all the same shape (an anisotropic
      zoom, which `zoompan` cannot express at all), or if the source
      cannot supply a frame of the needed aspect containing the whole path.
* **Return type:**
  [*tuple*](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[*Window*](#looks.motion.Window) | *None*, [*tuple*](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[*Keyframe*](#looks.motion.Keyframe), …]]

### looks.motion.zoompan_fragment(keyframes, , output, fps, aspect_tolerance=1e-06)

A path whose window size varies, compiled to `zoompan`.

* **Parameters:**
  * **output** ([`Size`](looks.geometry.html.md#looks.geometry.Size)) – The delivery size. `zoompan` must be told one — it resamples
    the window to a fixed output rather than emitting the window’s own
    pixels.
  * **fps** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – **The source’s frame rate**, required rather than defaulted.
    `zoompan`’s own default is 25, and passing the wrong one preserves
    the frame *count* while restamping it: 20 frames at 10 fps became 20
    frames at 25 fps, i.e. a 2.0 s clip silently became 0.8 s. A frame
    count check — the obvious check — passes in both cases.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

```pycon
>>> zoompan_fragment(
...     [Keyframe(0, Window.full()), Keyframe(2, Window(0.25, 0.25, 0.5, 0.5))],
...     output=Size(1920, 1080), fps=30,
... )
"zoompan=d=1:s=1920x1080:fps=30:z='1/(1+(-0.5)*min(max((in_time-0)/2,0),1))':x='iw*(0+(0.25)*min(max((in_time-0)/2,0),1))':y='ih*(0+(0.25)*min(max((in_time-0)/2,0),1))'"
```

* **Raises:**
  [**MotionError**](#looks.motion.MotionError) – If any window is not geometrically similar to the source
      frame. `zoom` is a single scalar, so the visible region is always
      `(iw/zoom, ih/zoom)` — one axis cannot be zoomed differently from
      the other, and honouring one while distorting the other silently is
      the failure this refuses.
* **Return type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.motion.zooms(keyframes)

Does the window’s SIZE change? That is the question that picks a filter.

```pycon
>>> full, half = Window.full(), Window(0.25, 0.25, 0.5, 0.5)
>>> zooms([Keyframe(0, full), Keyframe(2, half)])
True
```

A pan is a move at constant size, and does not zoom:

```pycon
>>> zooms([Keyframe(0, Window(0, 0, 0.5, 1)), Keyframe(2, Window(0.5, 0, 0.5, 1))])
False
```

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)
