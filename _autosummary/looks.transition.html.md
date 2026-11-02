# looks.transition

How one shot gives way to the next — the vocabulary, not the graph.

ffmpeg’s `xfade` offers 58 transitions on this build. This package carries
**sixteen**, and the reason is the posture rather than the number: a name a
caller passes should be refused here, at the boundary, rather than discovered
three stages later as an ffmpeg error. Measured — an unrecognised curve produces

> [Parsed_xfade_0] const_values array too small for transition
> Error applying option ‘transition’ to filter ‘xfade’:

> > Not yet implemented in FFmpeg, patches welcome

which names neither the caller’s mistake nor the filter’s actual complaint. A
vocabulary we own is a vocabulary we can keep working across ffmpeg builds, and
translating at the boundary is the same rule `muvid`’s EDL and `an`’s camera
table already follow.

### Why this module emits no filter

Every other compiler here returns a string. This one returns **options**, because
`xfade` takes *two* video inputs and a compiled fragment in this package
references no input index at all — that is rule 20, and it is what lets a
fragment splice into a bare `-vf`, into a per-cut chain, and into a pipe’s
encoder half alike. A two-input filter cannot satisfy it.

So `looks` owns the curve names, the record, and the floor; the host owns the
filtergraph that wires two streams into an `xfade`. That is the same split as
everywhere else: this package decides *what*, the caller decides *where*.

### A short transition is a hard cut wearing a label, and the floor is not a constant

Measured counting frames that are neither source colour. The numbers below
were taken on ffmpeg 8.1 and re-verified unchanged on **6.1.6 and 9.0.1**,
which is why they are stated as a property of the filter rather than of a
build — `speed=0` and a height-1 frame both looked like properties of ffmpeg
until CI ran a different one:

|   fps | duration   | blended frames   |
|-------|------------|------------------|
|    30 | 0.30 s     | 8                |
|    30 | 0.10 s     | 2                |
|    30 | 0.04 s     | 1                |
|    30 | 0.033 s    | **0**            |
|    10 | 0.30 s     | 2                |
|    10 | 0.10 s     | **0**            |

So a transition shorter than about one frame period produces \*\*no blended frame
at all\*\* — the picture cuts, and the record says it faded. `duration=0` is
accepted by ffmpeg without complaint.

[`MIN_TRANSITION_S`](#looks.transition.MIN_TRANSITION_S) is inherited from `muvid` at 0.04 s, which is exactly
one frame at 25 fps — which is where the number came from, and why it is \*too
small\* at lower rates. [`blended_frames()`](#looks.transition.blended_frames) is the honest form: it takes the
rate, because the question does.

### Module Attributes

| [`TRANSITION_CURVES`](#looks.transition.TRANSITION_CURVES)   | a curated subset of ffmpeg's 58, chosen because they read as deliberate edits rather than as effects.   |
|----------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------|
| [`DFLT_CURVE`](#looks.transition.DFLT_CURVE)          | The default curve.                                                                                      |
| [`MIN_TRANSITION_S`](#looks.transition.MIN_TRANSITION_S)    | The floor below which a transition is a hard cut wearing a label.                                       |
| [`XFADE_KIND`](#looks.transition.XFADE_KIND)          | ```<br/>`<br/>```<br/><br/>Transition.                                                                  |
| [`RIPPLE_KIND`](#looks.transition.RIPPLE_KIND)         | The `kind` a [`Ripple`](#looks.transition.Ripple) document carries, and must.        |

### Functions

| [`blended_frames`](#looks.transition.blended_frames)(transition, fps, \*[, offset])     | How many frames will be a mixture of the two shots.              |
|----------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| [`check_visible`](#looks.transition.check_visible)(transition, fps, \*[, offset])      | Raise unless the transition will actually be seen.               |
| [`is_hard_cut`](#looks.transition.is_hard_cut)(transition, fps, \*[, offset])        | Will this transition produce no blended frame at all?            |
| [`max_blended_frames`](#looks.transition.max_blended_frames)(transition, fps)               | The most frames this transition can blend, over every offset.    |
| [`xfade_options`](#looks.transition.xfade_options)(transition, \*, offset[, fps, ...]) | The `xfade` options for this transition — options, not a filter. |

### Classes

| [`Ripple`](#looks.transition.Ripple)(duration_s[, amplitude, wavelengths, ...])   | A dream transition: the picture ripples, blooms and dissolves into the next.   |
|------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------|
| [`Transition`](#looks.transition.Transition)(duration_s[, curve])                     | How a shot blends in from its predecessor.                                     |

### Exceptions

| [`TransitionError`](#looks.transition.TransitionError)   | A transition that cannot be honoured as asked.   |
|--------------------------------------------------------------------|--------------------------------------------------|

### looks.transition.DFLT_CURVE *= 'fade'*

The default curve. A plain cross-fade, because it is the one that reads as
no decision at all.

### looks.transition.MIN_TRANSITION_S *= 0.04*

The floor below which a transition is a hard cut wearing a label. Inherited
from `muvid`, where it is 0.04 s — **exactly one frame at 25 fps**, which is
where the number comes from. It is therefore too small at lower rates, and
[`blended_frames()`](#looks.transition.blended_frames) is the form that knows it: prefer that when the rate
is available, and treat this as the rate-free fallback it is.

### looks.transition.RIPPLE_KIND *= 'ripple'*

The `kind` a [`Ripple`](#looks.transition.Ripple) document carries, and must.

### *class* looks.transition.Ripple(duration_s, amplitude=0.017578125, wavelengths=(0.14930555555555555, 0.057291666666666664), bloom=0.55)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A dream transition: the picture ripples, blooms and dissolves into the next.

Not a [`TRANSITION_CURVES`](#looks.transition.TRANSITION_CURVES) name, because `xfade` cannot move a
pixel. It is two things the host already knows how to place, over one
window:

* [`dissolve`](#looks.transition.Ripple.dissolve), an ordinary [`Transition`](#looks.transition.Transition) for the host’s
  `xfade`, as for any other transition. It is `xfade`’s linear
  `fade`; the production this came from (issue #49) used a smoothstep
  blend, which no [`TRANSITION_CURVES`](#looks.transition.TRANSITION_CURVES) name gives.
* [`effect()`](#looks.transition.Ripple.effect), a single-input `ripple` effect, swelling from nothing
  at the window’s start to its peak at the middle of the fade and settling
  by its end. It compiles through [`looks.compile_look()`](looks.html.md#looks.compile_look) like any
  effect, so it carries a licence tier.

**Where the effect goes.** On the stream that holds *both* shots across the
window, the composite the dissolve produces, with `offset` the dissolve’s
start in *that stream’s own timeline*, after any `setpts` the host
applies. Two traps, both silent. A stream holding only the *incoming*
shot is the wrong one: `reeleehq/mixing`’s `_entrance` cross-fades a
cutaway from a transparent copy of itself, so its `xfade` output holds
the cutaway alone, and a ripple there would never move the outgoing scene.
In `mixing` the stream with both shots exists only after the overlay (a
post-overlay chain, the seam of reeleehq/mixing#115), with `offset=t0`.
And a host that cross-fades at offset 0 and then shifts the result with
`setpts` must pass the shifted start; the unshifted 0 runs the ripple on
the wrong frames.

**What it cannot do.** A window of about one frame period or less blends
nothing and ripples on at most one frame: call
[`check_visible()`](#looks.transition.check_visible) on [`dissolve`](#looks.transition.Ripple.dissolve) with the rate. The bloom’s blur
is sized from [`ClipSpec.height`](looks.spec.html.md#looks.spec.ClipSpec) at compile
time, while the warp scales with the frame at run time, so compile against
the clip the effect will actually run on. The motion’s phases are counted
from the window’s start, so the same record is the same picture wherever
the window lands.

Sizes are fractions of the frame (`amplitude` of its width,
`wavelengths` of its height), so a look reads the same at any resolution;
the defaults are 18 px and 86/33 px at 1024x576, judged on real footage.

### Examples

```pycon
>>> r = Ripple(1.0)
>>> r.dissolve
Transition(duration_s=1.0, curve='fade')
>>> e = r.effect(offset=6.3)
>>> e.name, e.params["start_s"], e.params["duration_s"]
('ripple', 6.3, 1.0)
>>> r.to_dict()["kind"]
'ripple'
>>> Ripple.from_dict(r.to_dict()) == r
True
>>> Ripple(1.0, bloom=2)
Traceback (most recent call last):
...
looks.transition.TransitionError: ripple: bloom must be a number in [0, 1]; got 2
```

A stored cross-fade is not read as a ripple, nor a ripple as a fade:

```pycon
>>> Ripple.from_dict({"duration_s": 1.0, "curve": "fade"})
Traceback (most recent call last):
...
looks.transition.TransitionError: not a Ripple document...
>>> Transition.from_dict(r.to_dict())
Traceback (most recent call last):
...
looks.transition.TransitionError: not a Transition document...
```

#### *property* dissolve *: [Transition](#looks.transition.Transition)*

The cross-fade the host runs between the two shots.

#### effect(, offset)

The warp, for the stream that holds both shots across the window.

`offset` is the dissolve’s start in *that* stream’s own timeline: the
number passed to `xfade` ([`xfade_options()`](#looks.transition.xfade_options)) when the effect runs
on `xfade`’s output directly, or the shifted start when the host
moves that output with `setpts` first (see the class docstring). The
warp’s peak then lands on the fade’s midpoint.

* **Return type:**
  [`Effect`](looks.spec.html.md#looks.spec.Effect)

#### *classmethod* from_dict(d)

A stored Ripple. An unknown key is refused, not ignored: a misspelt
`amplitde`, or a field from a newer version, would otherwise render
a different picture from the one stored.

* **Return type:**
  [`Ripple`](#looks.transition.Ripple)

### looks.transition.TRANSITION_CURVES *= frozenset({'circleclose', 'circleopen', 'dissolve', 'fade', 'fadeblack', 'fadewhite', 'slidedown', 'slideleft', 'slideright', 'slideup', 'smoothleft', 'smoothright', 'wipedown', 'wipeleft', 'wiperight', 'wipeup'})*

a curated subset of ffmpeg’s 58, chosen
because they read as deliberate edits rather than as effects. Adding one is a
decision — the point of an owned vocabulary is that it does not grow by
accident — and every name here is verified present in ffmpeg’s `xfade`.

* **Type:**
  The transitions this package offers

### *class* looks.transition.Transition(duration_s, curve='fade')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

How a shot blends in from its predecessor.

A record rather than a bare float, so the curve — and anything after it — is
an additive field rather than another shape change on something already
serialised.

The transition belongs to the shot it is *on*: it annotates that shot’s
**entrance**. `muvid`’s EDL keeps it that way so spans stay one per span, and
the reasoning for that invariant stays there — this is the vocabulary, not
the edit model.

### Examples

```pycon
>>> Transition(0.5)
Transition(duration_s=0.5, curve='fade')
>>> Transition(0.5, 'circleopen').curve
'circleopen'
```

A name outside the vocabulary is refused here, not by ffmpeg later:

```pycon
>>> Transition(0.5, 'starwipe')
Traceback (most recent call last):
...
looks.transition.TransitionError: 'starwipe' is not a transition this
package offers...
```

And a duration that cannot be a transition:

```pycon
>>> Transition(0.0)
Traceback (most recent call last):
...
looks.transition.TransitionError: a transition needs a positive
duration; got 0.0...
```

### *exception* looks.transition.TransitionError

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

A transition that cannot be honoured as asked.

### looks.transition.XFADE_KIND *= 'xfade'*

`Transition.
to_dict` writes none, so a document without one is an `xfade` transition;
any other kind is refused rather than read as a fade.

* **Type:**
  The `kind` a [`Transition`](#looks.transition.Transition) document may carry.
* **Type:**
  meth

### looks.transition.blended_frames(transition, fps, , offset=None)

How many frames will be a mixture of the two shots.

\*\*This is a GUARANTEED MINIMUM unless you pass `offset``**, and that is not
a hedge — the count genuinely depends on where the transition starts. A
frame blends when its time ``k/fps` falls strictly inside
`(offset, offset + duration)`; an open interval of length `D` contains at
least `ceil(D) - 1` integers and at most `floor(D)`, and which one you
get is decided by the offset’s fractional position. Measured against ffmpeg:
0.10 s at 30 fps blends **2** frames at `offset=0.5` and **3** at
`offset=0.42`.

An earlier version returned `floor(D) - 1` and described it as the count.
That is below the true minimum whenever `D` is not an integer, so it
under-reported — the safe direction for [`is_hard_cut()`](#looks.transition.is_hard_cut), but it
contradicted this module’s own measured table (0.04 s at 30 fps blends 1
frame; the formula said 0) and the tests never noticed because every row in
the parametrisation sat where the two formulas happen to agree.

```pycon
>>> blended_frames(Transition(0.30), 30)          # at least
8
>>> blended_frames(Transition(0.30), 30, offset=0.5)   # exactly
8
>>> blended_frames(Transition(0.10), 10)
0
>>> blended_frames(Transition(0.10), 30, offset=0.5)
2
>>> blended_frames(Transition(0.10), 30, offset=0.42)
3
```

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

### looks.transition.check_visible(transition, fps, , offset=None)

Raise unless the transition will actually be seen.

Call it when the rate is known. A transition that blends nothing is not a
subtle transition — it is a cut, and a record saying otherwise is the kind
of quiet disagreement between plan and picture this package exists to
prevent.

```pycon
>>> check_visible(Transition(0.30), 30)
>>> check_visible(Transition(0.05), 10)
Traceback (most recent call last):
...
looks.transition.TransitionError: a 0.05 s transition at 10 fps blends 0
frames...
```

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### looks.transition.is_hard_cut(transition, fps, , offset=None)

Will this transition produce no blended frame at all?

Without `offset` this is “might it blend nothing, at some offset” — the
conservative reading, since [`blended_frames()`](#looks.transition.blended_frames) returns the minimum.
With one it is the exact answer for that placement.

```pycon
>>> is_hard_cut(Transition(0.30), 30)
False
>>> is_hard_cut(Transition(0.10), 10)
True
```

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### looks.transition.max_blended_frames(transition, fps)

The most frames this transition can blend, over every offset.

The companion to [`blended_frames()`](#looks.transition.blended_frames)’ minimum. The pair is what makes the
uncertainty legible instead of hiding it inside a single number that is
right for one offset.

An open interval of length `D` contains at most `ceil(D)` integers —
NOT `floor(D)`, which is what intuition offers and what the first draft of
this function returned. A 0.04 s transition at 10 fps spans 0.4 of a frame
period and still blends one frame when it straddles a frame time
(`offset=0.17` puts the window at (1.7, 2.1), which contains 2). The
bracket test caught it.

```pycon
>>> blended_frames(Transition(0.25), 30), max_blended_frames(Transition(0.25), 30)
(7, 8)
>>> blended_frames(Transition(0.04), 10), max_blended_frames(Transition(0.04), 10)
(0, 1)
```

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

### looks.transition.xfade_options(transition, , offset, fps=None, first_clip_s=None)

The `xfade` options for this transition — options, not a filter.

`xfade` takes two video inputs, and a compiled fragment in this package
references no input index (rule 20). So the host wires the two streams and
splices these options in; `looks` says what the transition IS.

* **Parameters:**
  * **offset** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – When the transition starts, in the output’s timeline. The host’s
    number, because it depends on how the host laid out its cuts.
  * **fps** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]) – When given, the transition is checked against it — a transition
    that blends nothing is refused rather than emitted.
  * **first_clip_s** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]) – The duration of the stream the transition starts in. When
    given, an offset the clip cannot reach is refused. ffmpeg does NOT
    refuse it: measured on two 1.0 s clips, `offset=1.5` exits 0 and
    blends nothing — a fade in the record and a cut on screen, which is
    the same failure a zero duration is refused for.
* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### Examples

```pycon
>>> xfade_options(Transition(0.5, 'circleopen'), offset=2.0)
{'transition': 'circleopen', 'duration': 0.5, 'offset': 2.0}
```

```pycon
>>> xfade_options(Transition(0.02), offset=1.0, fps=25)
Traceback (most recent call last):
...
looks.transition.TransitionError: a 0.02 s transition at 25 fps blends 0
frames...
```
