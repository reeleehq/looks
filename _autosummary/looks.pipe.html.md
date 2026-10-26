# looks.pipe

A plan that mixes backends, as a pipe — emitted as data, never spawned.

Some effects are filters and some are Python over raw frames. A plan holding
both cannot be one ffmpeg process, so it becomes a **pipe**: ffmpeg decodes and
filters, hands raw frames to a Python operation, and a second ffmpeg reads those
frames back and filters again.

This module produces that arrangement **as data** — argv lists a caller can run.
`looks` does not run it, and structurally cannot: `looks._run` refuses any argv
whose outputs are not `-f null -`, and both halves emitted here are refused by
it. That is asserted rather than assumed, because “we simply do not call it” is
a convention and a refusal is a mechanism.

### What is deliberately not emitted

**The codec, the container, the output path.** The encoder half stops at its
input contract and its filter chain. Encode settings are a delivery decision the
host owns — `muvid` pins `-video_track_timescale` for concat compatibility, and
a package that grew opinions about `-c:v` would be the second muvid. It also
means no module here contains an encoder spelling, which the package’s own AST
perimeter scan enforces on every run.

### The fold, and the one place it is dangerous

Adjacent same-backend steps merge into one filter chain, and a filter run
*next to* a frame operation does not get its own process — it rides in the
`-vf` of the ffmpeg that already exists to feed or drain the pipe. That is what
makes a chain like Que Calor’s one (decoder, encoder) pair rather than three
processes.

Folding into the **decoder** half is always safe: it reads a container and
inherits the host’s filter timeline. Folding into the **encoder** half is not,
and this is rule 27:

> The encoder half reads `-f rawvideo`, which carries no timestamps at all.
> Its filter timeline restarts at 0.

So a step gated to “4 s to 5 s” fires on source frames 40-50 unfolded and on
**nothing at all** folded — exit 0, empty stderr, and a look that silently never
appears. Reproduced, and reproduced again with the rebase applied, which
restores a frame-for-frame identical result.

`looks` therefore **rebases what it can and refuses what it cannot**:

- A span carried structurally on `at` is one subtraction,
  and `looks` owns every expression it generates, so the rebase is exact.
- An `enable=` baked into a filter string by someone else is an arbitrary ffmpeg
  expression. Rewriting it would mean surgery on a grammar with no way to check
  the result, so it is refused by name.

And an undeclared origin is refused rather than assumed to be 0 — see
[`origin_s`](looks.spec.html.md#looks.spec.ClipSpec.origin_s), which is where that fact lives.

### Module Attributes

| [`DFLT_PIPE_PIX_FMT`](#looks.pipe.DFLT_PIPE_PIX_FMT)    | it is what the frame kernels in this ecosystem already speak, and packing means a frame is one contiguous `width * height * 3` read with no plane arithmetic.   |
|-----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`PIPE_BYTES_PER_PIXEL`](#looks.pipe.PIPE_BYTES_PER_PIXEL) | Bytes per pixel, by raw pixel format.                                                                                                                           |

### Functions

| [`describe`](#looks.pipe.describe)(arranged)                           | The arrangement as a few lines — what will run, and what it costs.     |
|-----------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| [`pipe_plan`](#looks.pipe.pipe_plan)(plan, \*, source[, clip, pix_fmt]) | Arrange a compiled plan as processes — emitted as data, never started. |
| [`piped_size`](#looks.pipe.piped_size)(clip, folded)                     | The frame size the decoder actually emits, after the folded chain.     |
| [`runs`](#looks.pipe.runs)(plan)                                   | Maximal runs of consecutive steps sharing a backend.                   |

### Classes

| [`FilterSegment`](#looks.pipe.FilterSegment)(vf)                              | A run of ffmpeg steps with no frame operation in it: one `-vf`.   |
|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------|
| [`FrameSegment`](#looks.pipe.FrameSegment)(op, decode, encode, pix_fmt, ...) | One ffmpeg → Python → ffmpeg segment.                             |
| [`PipePlan`](#looks.pipe.PipePlan)(segments, boundaries[, source])       | The whole arrangement, as data.                                   |

### Exceptions

| [`PipeError`](#looks.pipe.PipeError)   | A plan that cannot be arranged as a pipe, or not safely.   |
|--------------------------------------------------------------|------------------------------------------------------------|

### looks.pipe.DFLT_PIPE_PIX_FMT *= 'bgr24'*

it is what the
frame kernels in this ecosystem already speak, and packing means a frame is
one contiguous `width * height * 3` read with no plane arithmetic.

* **Type:**
  The raw pixel format the pipe carries. Packed 8-bit BGR

### *class* looks.pipe.FilterSegment(vf)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A run of ffmpeg steps with no frame operation in it: one `-vf`.

### *class* looks.pipe.FrameSegment(op, decode, encode, pix_fmt, width, height, rate, params=dict())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One ffmpeg → Python → ffmpeg segment.

Both argv are input-and-filter only. The caller appends its own encode
settings and destination to `encode`.

#### *property* frame_bytes *: [int](https://docs.python.org/3/builtins/functions.html#int)*

How many bytes one frame occupies on the pipe.

rawvideo has no header, so a consumer that guesses this reads a sheared
picture rather than an error.

### looks.pipe.PIPE_BYTES_PER_PIXEL *= {'abgr': 4, 'argb': 4, 'bgr24': 3, 'bgra': 4, 'gray': 1, 'rgb24': 3, 'rgba': 4}*

Bytes per pixel, by raw pixel format. A consumer sizes its reads from the
plan rather than from a constant it happens to agree on — rawvideo has no
header, so a wrong stride is a silently sheared picture rather than an error.
Only packed 8-bit formats are listed: a planar or higher-depth format has no
single bytes-per-pixel, so it is refused rather than approximated.

### *exception* looks.pipe.PipeError

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

A plan that cannot be arranged as a pipe, or not safely.

### *class* looks.pipe.PipePlan(segments, boundaries, source=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The whole arrangement, as data.

`boundaries` is the number of raw-frame crossings, which is the number
that costs — each one is a full decode and re-encode. It is reported after
folding, because counting runs before folding overstates it.

### looks.pipe.describe(arranged)

The arrangement as a few lines — what will run, and what it costs.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.pipe.pipe_plan(plan, , source, clip=None, pix_fmt='bgr24')

Arrange a compiled plan as processes — emitted as data, never started.

* **Parameters:**
  * **source** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – What the first decoder reads. Passed through verbatim; `looks`
    does not open it.
  * **clip** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`ClipSpec`](looks.spec.html.md#looks.spec.ClipSpec)]) – The clip the plan was compiled against. Defaults to the plan’s own.
* **Raises:**
  [**PipeError**](#looks.pipe.PipeError) – If the plan needs a raw-frame boundary and cannot be arranged
      safely across it — an undeclared time origin under a gated step, or
      a gate baked into a filter string.
* **Return type:**
  [`PipePlan`](#looks.pipe.PipePlan)

### Examples

A plan of pure ffmpeg steps is one segment and costs no boundary. The
plan is built here by hand rather than compiled, so the example needs no
ffmpeg — a doctest that needs a binary is a doctest CI does not run.

```pycon
>>> from looks.licence import Tier, terms_for
>>> from looks.spec import ImplRef, LookPlan, Step
>>> impl = ImplRef(effect='blur', impl='blur.ffmpeg.gblur',
...                backend='ffmpeg', terms=terms_for('ffmpeg')[0])
>>> plan = LookPlan(steps=(Step(effect='blur', impl=impl,
...     tier=Tier.COPYLEFT_TOOL, payload={'filter': 'gblur=sigma=2'}),))
>>> arranged = pipe_plan(plan, source='in.mp4')
>>> len(arranged), arranged.boundaries
(1, 0)
```

### looks.pipe.piped_size(clip, folded)

The frame size the decoder actually emits, after the folded chain.

An effect that changes the frame’s geometry declares `out_size` in its
payload. That is a **contract**, not decoration: rawvideo has no header, so
the size a consumer reads has to come from the plan, and an implementation
that resizes without saying so makes the declared stride a lie.

```pycon
>>> from looks.spec import ClipSpec
>>> piped_size(ClipSpec(width=640, height=480, fps=10), [])
(640, 480)
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`int`](https://docs.python.org/3/builtins/functions.html#int)]

### looks.pipe.runs(plan)

Maximal runs of consecutive steps sharing a backend.

The first thing the fold needs, and worth its own name because “how many
processes does this plan cost” is answered from it.

```pycon
>>> from looks.spec import LookPlan
>>> runs(LookPlan())
()
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Step`](looks.spec.html.md#looks.spec.Step), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]], [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]
