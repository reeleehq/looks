# looks.ffmpeg

The ffmpeg backend: filter strings, escaping, and the first effects.

This is where a `Step`’s payload becomes text another process will parse, which
is the whole reason the escaping in here is not a detail. Everything else in the
package produces data; this module produces a *string handed to a parser*, and
the flagship effect takes a caller-supplied file path.

### Escaping, and why once is not enough

ffmpeg unescapes a filter option **twice**. The filtergraph parser reads the
whole graph first, splitting on `,` `;` `[` `]` and consuming one layer
of quoting; only then is each surviving per-filter argument split into options
on `:`, consuming a second. So escaping runs in the **mirror order** — option
level first, graph level over that result — and each ffmpeg pass peels off
exactly one layer.

Ported from `muvid.visualize.canvas.escape_filter_value`, with its recorded
negative kept: **\`\`%\`\` is deliberately not escaped.** Neither parser treats it
as special, so `\%` was simply unescaped back to `%` and escaping it never
did anything. `drawtext`’s `%{...}` expansion is a third level belonging to
one filter’s `text` option, and is out of scope for a general escaper.

Verified here rather than inherited: `-vf "lut3d=file=id,with:comma.cube"`
fails, and the escaped form works.

### LGPL first, and the alternate says why

Where an effect has both a GPL-gated and an LGPL implementation, \*\*both are
registered\*\* and the LGPL one carries the lower `preference`. That is not a
licence judgement made here — the registry records what exists and a
[`Policy`](looks.licence.html.md#looks.licence.Policy) refuses at selection — it is an ordering, so that
a caller who never thinks about licences gets the portable answer by default and
a caller who needs the GPL one can still pin it.

`eq` is the case worth naming: the obvious grade filter is GPL-only, three of
its jobs have LGPL substitutes in the same binary, and `muvid` ships a single
`eq=` for a cosmetic dim. That one filter call is the concrete argument for
this package existing.

### What is deliberately absent

No encoder arguments, no output file, no process. A payload here is a filter
fragment and nothing more — the moment this module grows an opinion about
`-c:v` it has become the second muvid, and the `-f null -` invariant that
keeps the package honest would have nothing left to protect.

### Module Attributes

| [`OPTION_LEVEL_SPECIALS`](#looks.ffmpeg.OPTION_LEVEL_SPECIALS)   | Characters the **option** parser gives meaning to, within one filter's arguments.                                                                                   |
|--------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`GRAPH_LEVEL_SPECIALS`](#looks.ffmpeg.GRAPH_LEVEL_SPECIALS)    | Characters the **filtergraph** parser gives meaning to across the graph: `,` chains, `;` separates, `[]` delimit pad labels, `\\` and `'` do that parser's quoting. |
| [`RGB_DOMAIN_FILTERS`](#looks.ffmpeg.RGB_DOMAIN_FILTERS)      | Filters that only take RGB, so ffmpeg converts YUV to RGB and back around them.                                                                                     |
| [`RGB_ONLY_IMPL_VERSION`](#looks.ffmpeg.RGB_ONLY_IMPL_VERSION)   | The version of an implementation that sits in an RGB-only run.                                                                                                      |
| [`SETSAR_MAX`](#looks.ffmpeg.SETSAR_MAX)              | `setsar`'s largest allowed rational term.                                                                                                                           |
| [`LABEL_NAMESPACE`](#looks.ffmpeg.LABEL_NAMESPACE)         | Prefix of the pad labels a branching effect uses internally, so they stay clear of a host's own (`[a]`, `[bg]`: note 05, label rule 2).                             |

### Functions

| [`escape_filter_value`](#looks.ffmpeg.escape_filter_value)(value)     | Escape a value for use as a filter option inside a filtergraph.     |
|---------------------------------------------------------------------------------|---------------------------------------------------------------------|
| [`filter_string`](#looks.ffmpeg.filter_string)(name[, options]) | One filter, with its options escaped.                               |
| [`gated`](#looks.ffmpeg.gated)(fragment, at)            | Restrict a fragment to a span, using ffmpeg's own timeline support. |
| [`has_scale_matrix`](#looks.ffmpeg.has_scale_matrix)(color_space)  | Whether a declared colour space names a matrix `scale` knows.       |
| [`is_rgb_domain`](#looks.ffmpeg.is_rgb_domain)(filters)         | Whether any of these ffmpeg filters only takes RGB.                 |
| [`register_defaults`](#looks.ffmpeg.register_defaults)([registry])  | Register the built-in ffmpeg effects.                               |
| [`split_filters`](#looks.ffmpeg.split_filters)(fragment)        | A chain into its filters, splitting on UNESCAPED commas only.       |
| [`vf`](#looks.ffmpeg.vf)(plan, \*[, gate])           | A whole plan as one `-vf` fragment: input-index-free, splice-ready. |

### Exceptions

| [`FfmpegBackendError`](#looks.ffmpeg.FfmpegBackendError)   | A step that cannot be expressed as a filter fragment.   |
|-----------------------------------------------------------------------|---------------------------------------------------------|

### *exception* looks.ffmpeg.FfmpegBackendError

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

A step that cannot be expressed as a filter fragment.

### looks.ffmpeg.GRAPH_LEVEL_SPECIALS *= ('\\\\', "'", ',', ';', '[', ']')*

Characters the **filtergraph** parser gives meaning to across the graph:
`,` chains, `;` separates, `[]` delimit pad labels, `\\` and `'`
do that parser’s quoting.

### looks.ffmpeg.LABEL_NAMESPACE *= 'lk_'*

Prefix of the pad labels a branching effect uses internally, so they stay
clear of a host’s own (`[a]`, `[bg]`: note 05, label rule 2).

### looks.ffmpeg.OPTION_LEVEL_SPECIALS *= ('\\\\', "'", ':')*

Characters the **option** parser gives meaning to, within one filter’s
arguments. Must lead with `\\`: the backslashes introduced for the later
characters must not themselves be escaped by the `\\` pass.

### looks.ffmpeg.RGB_DOMAIN_FILTERS *= frozenset({'ciescope', 'colorbalance', 'colorchannelmixer', 'colorcontrast', 'colorhold', 'colorkey', 'colorlevels', 'colortemperature', 'curves', 'dctdnoiz', 'despill', 'elbg', 'epx', 'exposure', 'grayworld', 'greyedge', 'histeq', 'hqx', 'huesaturation', 'lut1d', 'lut3d', 'lutrgb', 'normalize', 'palettegen', 'photosensitivity', 'rgbashift', 'selectivecolor', 'stereo3d', 'super2xsai', 'tonemap', 'vibrance', 'xbr'})*

Filters that only take RGB, so ffmpeg converts YUV to RGB and back around
them. On ffmpeg 6.1 that auto-inserted conversion ignores the colour tags:
a flat BT.709 frame lost about 7 luma through any of these, a colour test
pattern 6.4 mean luma (against 0.16 on ffmpeg 9), issue #29. A YUV-capable
filter (`lutyuv`, `gblur`) is untouched by it and so is not listed.

### looks.ffmpeg.RGB_ONLY_IMPL_VERSION *= '2'*

The version of an implementation that sits in an RGB-only run.

### looks.ffmpeg.SETSAR_MAX *= 2147483647*

`setsar`’s largest allowed rational term. Its default of 100 rewrites any
SAR with a bigger term (118/81 -> 67/46, 1001/1000 -> 1/1).

### looks.ffmpeg.escape_filter_value(value)

Escape a value for use as a filter option inside a filtergraph.

```pycon
>>> escape_filter_value("plain.cube")
'plain.cube'
```

A comma would end the filter and a colon would end the option, so both are
escaped twice — once for each parser that will read them:

```pycon
>>> escape_filter_value("id,with:comma.cube")
'id\\,with\\\\:comma.cube'
```

`%` is left alone, on purpose — neither parser treats it as special, so
escaping it only produced a backslash that was unescaped away again:

```pycon
>>> escape_filter_value("100%.cube")
'100%.cube'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.ffmpeg.filter_string(name, options=None)

One filter, with its options escaped.

```pycon
>>> filter_string("gblur", {"sigma": 2})
'gblur=sigma=2'
>>> filter_string("null")
'null'
```

A path with a comma in it survives, which is the whole point:

```pycon
>>> filter_string("lut3d", {"file": "a,b.cube"})
'lut3d=file=a\\,b.cube'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.ffmpeg.gated(fragment, at)

Restrict a fragment to a span, using ffmpeg’s own timeline support.

```pycon
>>> gated("gblur=sigma=2", None)
'gblur=sigma=2'
>>> gated("gblur=sigma=2", Span(1.0, 3.5))
"gblur=sigma=2:enable='between(t,1,3.5)'"
```

A fragment of several filters is gated **per filter**, because `enable` is
an option on a filter and not on a chain — writing it once at the end would
gate only the last one, silently:

```pycon
>>> gated("scale=2:2,crop=1:1", Span(0.0, 1.0))
"scale=2:2:enable='between(t,0,1)',crop=1:1:enable='between(t,0,1)'"
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.ffmpeg.has_scale_matrix(color_space)

Whether a declared colour space names a matrix `scale` knows.

The one predicate behind both the compile-time refusal (rule 22) and
`_matrix_wrap()`: `"unknown"` (what ffprobe prints for an untagged
stream) and any other unmapped name is *not* a declaration.

```pycon
>>> has_scale_matrix("bt709")
True
>>> has_scale_matrix("unknown")
False
>>> has_scale_matrix(None)
False
```

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### looks.ffmpeg.is_rgb_domain(filters)

Whether any of these ffmpeg filters only takes RGB.

This is what derives `ImplRef.rgb_only` for the built-ins; the
compiler and [`vf()`](#looks.ffmpeg.vf) read the flag, never this list.

```pycon
>>> is_rgb_domain(("curves",))
True
>>> is_rgb_domain(("gblur",))
False
```

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### looks.ffmpeg.register_defaults(registry=None)

Register the built-in ffmpeg effects. Idempotent per registry.

Called once on `import looks`. Pass your own registry to get an
independent set — the module-level default is the one
[`looks.compile.compile_look()`](looks.compile.html.md#looks.compile.compile_look) uses.

### Examples

```pycon
>>> reg = register_defaults(EffectRegistry())
>>> "saturation" in reg.effects() and "lut3d" in reg.effects()
True
```

Both ways to saturate are registered, and the LGPL one sorts first:

```pycon
>>> [i.impl for i in reg.implementations("saturation")]
['saturation.ffmpeg.colorchannelmixer', 'saturation.ffmpeg.eq']
```

* **Return type:**
  [`EffectRegistry`](looks.registry.html.md#looks.registry.EffectRegistry)

### looks.ffmpeg.split_filters(fragment)

A chain into its filters, splitting on UNESCAPED commas only.

A comma inside a filter option is escaped — rule 21, and this package’s own
[`escape_filter_value()`](#looks.ffmpeg.escape_filter_value) produces it routinely. Splitting on every comma
cuts *inside* an expression: the shipped `gamma` effect compiles to
`lutrgb=r=maxval*pow(val/maxval\,0.833333):...`, and the naive split
turned that into an unparseable chain the moment it was gated —
`pow(val/maxval\:enable='between(t,1,2)',0.83)`.

```pycon
>>> split_filters("scale=2:2,crop=1:1")
['scale=2:2', 'crop=1:1']
```

An escaped comma stays inside its filter:

```pycon
>>> split_filters(r"lutrgb=r=pow(val\,2),gblur=sigma=1") == [
...     r"lutrgb=r=pow(val\,2)", "gblur=sigma=1"]
True
```

An escaped BACKSLASH does not escape the comma after it:

```pycon
>>> split_filters("a=x\\\\,b=y") == ["a=x\\\\", "b=y"]
True
```

### looks.ffmpeg.vf(plan, , gate=True)

A whole plan as one `-vf` fragment: input-index-free, splice-ready.

The seam every consumer asked for is one string — `muvid` splices it into
the filter chain `_render_part` already builds, and that only works if
nothing here names a stream.

* **Raises:**
  [**FfmpegBackendError**](#looks.ffmpeg.FfmpegBackendError) – If a step is not ffmpeg-backed, or is gated to a
      span its filter cannot honour. The second is why
      [`timeline`](looks.spec.html.md#looks.spec.ImplRef.timeline) exists: `zoompan` and
      `elbg` carry no timeline support, so an `at` on them would be
      accepted by the string and ignored by the binary.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
