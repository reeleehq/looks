# looks.environment

What the ffmpeg on *this* machine actually is, and what it can actually do.

Two questions, two authorities, and they are not interchangeable:

- **What licence does this binary carry?** `ffmpeg -L`. Nothing else.
- **Which filters does it have?** `ffmpeg -filters`. Nothing else.

Both of those sentences are load-bearing, and both were established by
measurement rather than by reading documentation.

`ffmpeg -L` prints a licence statement produced by a compile-time `#if`
cascade in `fftools/opt_common.c`. That matters because the more obvious
source — the `configuration:` line in `ffmpeg -version` — is \*editable by
whoever built the binary\*, and at least one widely-installed wheel does edit
the licence conclusion out of it. PyAV’s bundled FFmpeg patches `configure`
to move `libx264`/`libx265` out of `EXTERNAL_LIBRARY_GPL_LIST`, so its
`avutil_license()` reports “LGPL version 3 or later” while `otool -L` shows
GPL `libx264` and `libx265` actually linked. A licence check that trusts a
self-report is not a check; `-L`’s cascade is the least-editable statement a
binary makes about itself, and even it is only evidence, not proof.

`ffmpeg -h filter=NAME` looks like a capability probe and is not one: on
ffmpeg 8.1 an unknown filter prints `Unknown filter 'x'.` and then, verbatim,
`Exiting with exit code 0`. Every filter would test as present. So
availability comes from parsing the `-filters` table.

And the rule that ties them together: \*\*anything this module cannot determine
is reported as unknown, and unknown is a refusal upstream.\*\* A build whose
licence line matches nothing known is not “probably LGPL”; it is unknown. The
functions here never guess and never raise on a merely-absent ffmpeg — they
return a [`FfmpegEnv`](#looks.environment.FfmpegEnv) that says so, because a caller diagnosing a missing
binary needs a value it can inspect, not a traceback.

\*\*There is not one ffmpeg on a machine, and the difference is not a version
number.\*\* Measured on this one: `PATH` carries ffmpeg 8.1, GPL-**3**, 481
filters; the binary `imageio-ffmpeg` ships inside site-packages is ffmpeg 7.1,
GPL-**2**, 484 filters — and the two filter sets are **non-nested**. Only PATH
has `colordetect`, `premultiply_dynamic`, `transpose_vt`,
`yadif_videotoolbox`; only the bundled one has `ass`, `drawtext`, `pp`,
`subtitles`, `vidstabdetect`, `vidstabtransform`, `zscale`. So neither
“the ffmpeg version” nor “the ffmpeg licence” is a single fact about a machine.

The rule that follows is the important one: \*\*a caller passes the environment
in; nothing downstream may call\*\* [`probe()`](#looks.environment.probe) **for itself.** A compiled Look
is valid against *one* [`FfmpegEnv`](#looks.environment.FfmpegEnv), not against a machine, and a
component that probes on its own behalf silently binds to whichever binary
happened to be first on `PATH` — which, for anything invoked through moviepy,
is not the one the user is looking at.

Nothing here executes a filter, decodes a frame, or writes a file. It runs
`ffmpeg` three times with no input and parses text.

```pycon
>>> env = probe()
>>> env.licence
<Licence.GPL3: 'gpl3'>
>>> env.has_filter('lut3d')
True
```

### Module Attributes

| [`DFLT_PROBE_TIMEOUT_S`](#looks.environment.DFLT_PROBE_TIMEOUT_S)   | these are trivial commands, so exceeding it means something is wrong (a network filesystem, a binary that hangs on a missing dylib) and we would rather say "unknown" than block a caller forever.   |
|-------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`DFLT_FFMPEG`](#looks.environment.DFLT_FFMPEG)            | The default binary name, looked up on `PATH`.                                                                                                                                                        |
| [`GATES_PATH`](#looks.environment.GATES_PATH)             | Where the committed gate table lives, relative to this package.                                                                                                                                      |
| [`LICENCE_ORDER`](#looks.environment.LICENCE_ORDER)          | Permissiveness order, most permissive first.                                                                                                                                                         |

### Functions

| [`gates`](#looks.environment.gates)()                         | The committed table of FFmpeg's own licence gates, extracted from source.                                                          |
|----------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| [`gpl_only_filters`](#looks.environment.gpl_only_filters)()              | Filter names FFmpeg gates behind `--enable-gpl`.                                                                                   |
| [`known_filters`](#looks.environment.known_filters)()                 | Every filter name FFmpeg n8.1 declares — the universe [`needs_gpl()`](#looks.environment.needs_gpl) checks against. |
| [`needs_gpl`](#looks.environment.needs_gpl)(filters, \*[, known]) | Which of `filters` exist only in a GPL build, in the order given.                                                                  |
| [`parse_configuration`](#looks.environment.parse_configuration)(text)       | Pull the `configuration:` line out of `ffmpeg -version` output.                                                                    |
| [`parse_filters`](#looks.environment.parse_filters)(text)             | Extract filter names from `ffmpeg -filters` output.                                                                                |
| [`parse_licence`](#looks.environment.parse_licence)(text)             | Classify `ffmpeg -L` output.                                                                                                       |
| [`probe`](#looks.environment.probe)([ffmpeg, timeout])        | Interrogate one ffmpeg binary.                                                                                                     |

### Classes

| [`EnvFingerprint`](#looks.environment.EnvFingerprint)(path, version, licence, ...)       | The part of an environment that determines pixels, as comparable data.   |
|----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------|
| [`FfmpegEnv`](#looks.environment.FfmpegEnv)([path, version, licence, filters, ...]) | One machine's ffmpeg, as far as it can be determined without running it. |
| [`Licence`](#looks.environment.Licence)(\*values)                                 | What licence an ffmpeg build carries, as `ffmpeg -L` reports it.         |

### Exceptions

| [`UnknownFilter`](#looks.environment.UnknownFilter)   | A filter name that is not in any known universe.   |
|------------------------------------------------------------------|----------------------------------------------------|

### looks.environment.DFLT_FFMPEG *= 'ffmpeg'*

The default binary name, looked up on `PATH`.

### looks.environment.DFLT_PROBE_TIMEOUT_S *= 20.0*

these are trivial
commands, so exceeding it means something is wrong (a network filesystem, a
binary that hangs on a missing dylib) and we would rather say “unknown” than
block a caller forever.

* **Type:**
  How long any single probe subprocess may take. Generous

### *class* looks.environment.EnvFingerprint(path, version, licence, filters_digest)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The part of an environment that determines pixels, as comparable data.

A [`LookPlan`](looks.spec.html.md#looks.spec.LookPlan) is compiled against **one binary**, whose
filter set and licence are part of what decides the output — so a plan says
which one, and this enters its hash. The portable artifact is the `Look`;
the plan is deliberately not portable, and this is the field that says so.

[`filters_digest`](#looks.environment.EnvFingerprint.filters_digest) is a hash rather than the set itself: the set is ~481
names, a plan is a document, and “which filters existed” only ever needs to
be compared, never read.

#### path

The resolved binary. Two ffmpegs on one machine is the normal
case, not the exotic one.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### version

Its version line.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### licence

What `ffmpeg -L` said.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### filters_digest

SHA-256 over the sorted filter names.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### Examples

```pycon
>>> a = EnvFingerprint(path='/usr/bin/ffmpeg', version='8.1',
...                    licence='gpl3', filters_digest='abc')
>>> a == EnvFingerprint(path='/usr/bin/ffmpeg', version='8.1',
...                     licence='gpl3', filters_digest='abc')
True
```

#### to_dict()

A JSON-able form, for a plan’s serialisation and its hash.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### *class* looks.environment.FfmpegEnv(path=None, version=None, licence=Licence.UNKNOWN, filters=frozenset({}), configuration=None, notes=())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One machine’s ffmpeg, as far as it can be determined without running it.

#### path

Resolved path to the binary, or `None` if none was found.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### version

The version string from `ffmpeg -version`’s first line, or
`None`.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### licence

What `ffmpeg -L` says. `Licence.UNKNOWN` whenever the
output matched nothing known, the binary was absent, or the probe
failed — three different reasons, one honest answer.

* **Type:**
  [`Licence`](#looks.environment.Licence)

#### filters

Every filter name `ffmpeg -filters` listed. Empty when the
probe failed, which is why [`available`](#looks.environment.FfmpegEnv.available) exists to tell “no
filters” apart from “did not look”.

* **Type:**
  [`frozenset`](https://docs.python.org/3/builtins/stdtypes.html#frozenset)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### configuration

The raw `configuration:` line, kept for diagnostics
only. **Never** read it to decide a licence — it is editable by the
builder, which is the whole reason [`licence`](#looks.environment.FfmpegEnv.licence) comes from
`-L`.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### notes

Human-readable reasons anything above is missing.

* **Type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

#### *property* available *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Whether an ffmpeg binary was found and answered at all.

Distinct from “has no filters”: a probe that could not run leaves
[`filters`](#looks.environment.FfmpegEnv.filters) empty too, and a caller must be able to tell those
apart before concluding anything.

#### fingerprint()

The comparable summary a compiled plan records.

* **Raises:**
  [**RuntimeError**](https://docs.python.org/3/builtins/exceptions.html#RuntimeError) – The probe did not run. A fingerprint of an
      environment nobody looked at would make two plans compiled
      against unknown binaries compare equal, which is the false
      direction.
* **Return type:**
  [`EnvFingerprint`](#looks.environment.EnvFingerprint)

### Examples

```pycon
>>> FfmpegEnv().fingerprint()
Traceback (most recent call last):
...
RuntimeError: cannot fingerprint an ffmpeg that did not answer...
```

#### has_filter(name)

Whether `name` is in this build’s filter table.

Always `False` when the probe did not run — check [`available`](#looks.environment.FfmpegEnv.available)
first if the difference matters to you.

### Examples

```pycon
>>> FfmpegEnv(filters=frozenset({'lut3d'})).has_filter('lut3d')
True
>>> FfmpegEnv(filters=frozenset({'lut3d'})).has_filter('eq')
False
```

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

#### missing(names)

Which of `names` this build does not have, in the order given.

### Examples

```pycon
>>> env = FfmpegEnv(filters=frozenset({'lut3d', 'curves'}))
>>> env.missing(['lut3d', 'eq', 'boxblur'])
('eq', 'boxblur')
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.environment.GATES_PATH *= PosixPath('/home/runner/work/looks/looks/looks/data/ffmpeg_gates.json')*

Where the committed gate table lives, relative to this package.

### looks.environment.LICENCE_ORDER *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[Licence](#looks.environment.Licence), ...]* *= (Licence.LGPL21, Licence.LGPL3, Licence.GPL2, Licence.GPL3, Licence.NONFREE)*

Permissiveness order, most permissive first. `Licence.UNKNOWN` is
absent on purpose — see [`Licence`](#looks.environment.Licence).

### *class* looks.environment.Licence(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

What licence an ffmpeg build carries, as `ffmpeg -L` reports it.

Ordered from most to least permissive by [`LICENCE_ORDER`](#looks.environment.LICENCE_ORDER). `UNKNOWN`
is deliberately *not* on that ladder: it is not a position between two
others, it is the absence of a position, and it must refuse rather than
compare.

### *exception* looks.environment.UnknownFilter

Bases: [`ValueError`](https://docs.python.org/3/builtins/exceptions.html#ValueError)

A filter name that is not in any known universe.

Raised rather than ignored, because [`needs_gpl()`](#looks.environment.needs_gpl) is an
**allowlist-by-absence**: a name it does not recognise carries no gate, so
silently returning “not GPL” for a typo, a wrong case, a filter from a newer
ffmpeg, or one an extraction never enumerated is a *computed* false
permission — at exactly the point the licence tier enters. That is the one
direction this package may never fail in.

### looks.environment.gates()

The committed table of FFmpeg’s own licence gates, extracted from source.

**A filter is GPL-gated two ways, and a grep finds only one of them.**
*Directly*, when its `_filter_deps` line contains the literal `gpl`
(33 filters, `eq` among them). *Indirectly*, when its deps name an
external library that is itself in `EXTERNAL_LIBRARY_GPL_LIST` — enabling
the filter then forces `--enable-gpl` transitively, with no `gpl` token
anywhere on its own line. Five filters are in that second class:
`frei0r`, `frei0r_src`, `rubberband`, `vidstabdetect`,
`vidstabtransform`.

Missing them is a **false permission**, which is the dangerous direction:
`vidstabtransform` is stabilisation, i.e. a perfectly plausible
normalisation effect for this package, and the naive extraction tiers it
permissive. The first version of this table did exactly that; it was caught
by an adversarial review rather than by any test, which is why the two
classes are now stored separately and asserted separately.

This is what FFmpeg’s `configure` *declares*, not what the local binary
*has* — the two answer different questions, and both are needed. The table
says an effect written with `eq` could never run on a clean-room LGPL
build; [`probe()`](#looks.environment.probe) says whether the binary in front of you happens to have
it. Collapsing them makes every purely-LGPL Look unrunnable on every
Homebrew ffmpeg on earth, since those are all GPL builds.

### Examples

```pycon
>>> g = gates()
>>> 'eq' in g['gpl_filters']
True
>>> 'geq' in g['gpl_filters']      # relicensed in FFmpeg 4.3
False
>>> 'lut3d' in g['gpl_filters']
False
>>> 'libx264' in g['external_gpl']
True
```

* **Return type:**
  [`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`object`](https://docs.python.org/3/builtins/functions.html#object)]

### looks.environment.gpl_only_filters()

Filter names FFmpeg gates behind `--enable-gpl`.

### Examples

```pycon
>>> f = gpl_only_filters()
>>> {'eq', 'boxblur', 'cropdetect'} <= f
True
>>> f & {'lut3d', 'curves', 'colorlevels', 'geq'}
frozenset()
```

* **Return type:**
  [`frozenset`](https://docs.python.org/3/builtins/stdtypes.html#frozenset)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### looks.environment.known_filters()

Every filter name FFmpeg n8.1 declares — the universe [`needs_gpl()`](#looks.environment.needs_gpl) checks against.

Extracted from `libavfilter/allfilters.c`, which declares one `extern`
per filter regardless of build flags, so it covers filters the local binary
does not have. That is the right universe: a name absent from *this* build
is still a real filter with a real gate, and refusing it would be a false
alarm, while a name absent from *FFmpeg* is a typo and must raise.

### Examples

```pycon
>>> u = known_filters()
>>> {'eq', 'lut3d', 'vidstabtransform', 'geq'} <= u
True
>>> 'nosuchfilter' in u
False
>>> len(u) > 500
True
```

* **Return type:**
  [`frozenset`](https://docs.python.org/3/builtins/stdtypes.html#frozenset)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### looks.environment.needs_gpl(filters, , known=None)

Which of `filters` exist only in a GPL build, in the order given.

The point of the package in one function: a chain that reaches for the
obvious grade filter is not portable to an LGPL build, and nothing in the
ffmpeg CLI will tell you, because the binary you are holding runs it fine.

**Every name is validated first, and an unrecognised one raises.** This
function is an allowlist-by-absence — a name carrying no gate is reported
GPL-free — so without the check a typo, a wrong case, or a filter from a
newer ffmpeg is a *computed false permission*. That is not a hypothetical:
before the check, `needs_gpl(['nosuchfilter'])` and `needs_gpl(['EQ'])`
both returned `()`.

* **Parameters:**
  * **filters** ([`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Filter names, in the order they appear in a chain.
  * **known** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`frozenset`](https://docs.python.org/3/builtins/stdtypes.html#frozenset)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]]) – The universe to validate against. Pass
    [`FfmpegEnv.filters`](#looks.environment.FfmpegEnv.filters) to also catch a name this build does not
    have; the default is [`known_filters()`](#looks.environment.known_filters), every filter FFmpeg
    n8.1 declares.
* **Raises:**
  [**UnknownFilter**](#looks.environment.UnknownFilter) – A name is not in `known`.
* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### Examples

```pycon
>>> needs_gpl(['scale', 'eq', 'lut3d', 'boxblur'])
('eq', 'boxblur')
>>> needs_gpl(['curves', 'colorlevels', 'lut3d'])
()
```

A name that is not a filter raises rather than reporting GPL-free:

```pycon
>>> needs_gpl(['nosuchfilter'])
Traceback (most recent call last):
...
looks.environment.UnknownFilter: not known ffmpeg filters: ['nosuchfilter']...
```

Case matters, because it matters to ffmpeg:

```pycon
>>> needs_gpl(['EQ'])
Traceback (most recent call last):
...
looks.environment.UnknownFilter: not known ffmpeg filters: ['EQ']...
```

### looks.environment.parse_configuration(text)

Pull the `configuration:` line out of `ffmpeg -version` output.

Diagnostics only. See [`FfmpegEnv.configuration`](#looks.environment.FfmpegEnv.configuration) for why this must
never decide a licence.

### Examples

```pycon
>>> parse_configuration("ffmpeg version 8.1\nconfiguration: --enable-gpl\n")
'--enable-gpl'
>>> parse_configuration("ffmpeg version 8.1\n") is None
True
```

* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### looks.environment.parse_filters(text)

Extract filter names from `ffmpeg -filters` output.

The samples below are **verbatim** ffmpeg output, not hand-written — an
invented sample is a test of the regex against itself, which is how the
first version of this parser passed its doctests while returning zero
filters from the real binary.

### Examples

Two-character flags, as ffmpeg 8.1 emits them:

```pycon
>>> eight = '''Filters:
...   T.. = Timeline support
...   .S. = Slice threading
...   ------
...  TS aap               AA->A      Apply Affine Projection algorithm.
...  .. abench            A->A       Benchmark part of a filtergraph.
...  TS lut3d             V->V       Adjust colors using a 3D LUT.
... '''
>>> sorted(parse_filters(eight))
['aap', 'abench', 'lut3d']
```

Three-character flags, as older builds emit them:

```pycon
>>> six = ' TSC lut3d            V->V       Adjust colors using a 3D LUT.'
>>> sorted(parse_filters(six))
['lut3d']
```

The legend lines are rejected because they carry no io signature:

```pycon
>>> parse_filters('  T.. = Timeline support')
frozenset()
```

* **Return type:**
  [`frozenset`](https://docs.python.org/3/builtins/stdtypes.html#frozenset)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### looks.environment.parse_licence(text)

Classify `ffmpeg -L` output.

Most-restrictive-first, because the licence names are prefixes of one
another: a permissive-first scan matches “GNU General Public License” inside
the GPLv3 text and reports GPLv2. Anything unmatched is
`Licence.UNKNOWN` — never a default, never a guess.

### Examples

```pycon
>>> parse_licence("ffmpeg is free software; ... GNU General Public "
...               "License as published by ... either version 3")
<Licence.GPL3: 'gpl3'>
>>> parse_licence("... GNU Lesser General Public License ... version 2.1")
<Licence.LGPL21: 'lgpl2.1'>
>>> parse_licence("this build is nonfree and unredistributable")
<Licence.NONFREE: 'nonfree'>
>>> parse_licence("")
<Licence.UNKNOWN: 'unknown'>
>>> parse_licence("Copyright (c) somebody, all rights reserved")
<Licence.UNKNOWN: 'unknown'>
```

* **Return type:**
  [`Licence`](#looks.environment.Licence)

### looks.environment.probe(ffmpeg='ffmpeg', , timeout=20.0)

Interrogate one ffmpeg binary. Three subprocess calls, no input, no output.

Returns a [`FfmpegEnv`](#looks.environment.FfmpegEnv) in every case, including when `ffmpeg` is not
installed — the absence of a binary is a fact about the machine, and a
caller diagnosing it needs a value rather than an exception.

* **Parameters:**
  * **ffmpeg** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Binary name (looked up on `PATH`) or an explicit path.
  * **timeout** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – Seconds allowed per probe call.
* **Return type:**
  [`FfmpegEnv`](#looks.environment.FfmpegEnv)

### Examples

```pycon
>>> env = probe('a-binary-that-does-not-exist')
>>> env.available
False
>>> env.licence
<Licence.UNKNOWN: 'unknown'>
>>> env.notes[0]
"no 'a-binary-that-does-not-exist' on PATH"
```
