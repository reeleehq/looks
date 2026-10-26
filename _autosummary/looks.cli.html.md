# looks.cli

The command line: thin adapters over the library, and no logic of its own.

Every function here converts strings to the library’s types, calls one library
function, and returns something printable. **None of them decides anything.**
If a rule lives in this module it is in the wrong place — a CLI is one surface
among several, and a refusal that only fires on the command line is not a
refusal.

Dispatched with [cw](https://pypi.org/project/cw/), which turns a mapping of
functions into an `argparse` parser by reading their signatures. Under
`cw.MODERN` rather than its argh-compatible default, because this package
annotates with `collections.abc` interfaces and argh recognises `list` and
nothing else — under the default, `looks check scale eq lut3d` bound one token
and reported the rest as unrecognised. Reading `Sequence[str]` as “several
values” is [i2mint/cw#36](https://github.com/i2mint/cw/pull/36), contributed
from here.

Two reasons for `cw` rather than the obvious alternatives, and both are this
package’s own thesis applied to itself:

- **\`argh\` is LGPL-3.0**, and its PyPI metadata `License:` field is *empty* —
  only the shipped `COPYING` / `COPYING.LESSER` pair says so. A package that
  refuses a dependency for a licence nobody’s tooling can see should not import
  one.
- **\`typer\` pulls six packages** into a distribution that declares stdlib only.

`cw` is MIT, declares `dependencies = []`, and — verified — `import cw`
pulls in nothing beyond stdlib: its `argcomplete` and `i2` imports are lazy,
inside the functions that need them. It is an optional extra here regardless,
so `import looks` never reaches it.

Everything below is analysis. The `-f null -` invariant covers the CLI like
everything else, because it goes through the same chokepoint.

> $ looks check scale eq lut3d
> eq
> $ echo $?
> 1

### Module Attributes

| [`EXIT_REFUSED`](#looks.cli.EXIT_REFUSED)   | the whole point is that a script can gate on it, and a refusal that exits 0 is a warning wearing a refusal's clothes.   |
|-----------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------------------|
| [`COMMANDS`](#looks.cli.COMMANDS)       | The command table.                                                                                                      |

### Functions

| [`check`](#looks.cli.check)(filters, \*[, ffmpeg, quiet])         | Which of these ffmpeg filters exist only in a GPL build?                   |
|----------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| [`disclaimer`](#looks.cli.disclaimer)()                                | What a tier is, and what it is not.                                        |
| [`env`](#looks.cli.env)([ffmpeg])                               | Report what the ffmpeg on this machine is, and what it may do.             |
| [`flicker`](#looks.cli.flicker)(chain)                              | Can this filter chain flicker? Decided by four probes, not by judgement.   |
| [`main`](#looks.cli.main)([argv])                                | Dispatch the command table.                                                |
| [`measure`](#looks.cli.measure)(clip, \*[, vf, frames])             | Measure a clip, optionally through a filter chain.                         |
| [`motion`](#looks.cli.motion)(keyframes, \*[, output, fps])        | Compile a camera path into an ffmpeg fragment.                             |
| [`place`](#looks.cli.place)(source, target, \*[, mode, backdrop]) | The ffmpeg chain that puts a WxH source into a WxH target.                 |
| [`terms`](#looks.cli.terms)(provider)                             | What is recorded about a provider's licence, and what tier it projects to. |
| [`unverified`](#looks.cli.unverified)()                                | What the licence ledger could NOT verify.                                  |

### looks.cli.COMMANDS *= {'check': <function check>, 'disclaimer': <function disclaimer>, 'env': <function env>, 'flicker': <function flicker>, 'measure': <function measure>, 'motion': <function motion>, 'place': <function place>, 'terms': <function terms>, 'unverified': <function unverified>}*

The command table. A callable value is a command; `cw` reads the signatures.

### looks.cli.EXIT_REFUSED *= 1*

the whole
point is that a script can gate on it, and a refusal that exits 0 is a
warning wearing a refusal’s clothes.

* **Type:**
  What `check` exits with when a filter needs a GPL build. Not 0

### looks.cli.check(filters, , ffmpeg=None, quiet=False)

Which of these ffmpeg filters exist only in a GPL build?

The headline. Prints one name per line and **exits non-zero** if any of them
needs a GPL ffmpeg, so a build script can gate on it.

An unrecognised filter name **raises** rather than reporting it clean: this
check is an allowlist-by-absence, so a typo would otherwise be a computed
false permission.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.cli.disclaimer()

What a tier is, and what it is not.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.cli.env(ffmpeg='ffmpeg')

Report what the ffmpeg on this machine is, and what it may do.

There is not one ffmpeg on a machine — pass `--ffmpeg` to ask a different
one, e.g. the binary a wheel bundled.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.cli.flicker(chain)

Can this filter chain flicker? Decided by four probes, not by judgement.

A verdict of `independent` is **evidence, not proof** — see
[`looks.frame_dependency`](looks.frame_dependency.html.md#module-looks.frame_dependency).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.cli.main(argv=None)

Dispatch the command table. The entry point for `looks ...`.

* **Raises:**
  [**SystemExit**](https://docs.python.org/3/builtins/exceptions.html#SystemExit) – With a message naming the extra, when `cw` is absent. It is
      an optional dependency: `import looks` must stay stdlib-only, so
      the CLI cannot be a hard requirement of the library.
* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

### looks.cli.measure(clip, , vf='', frames=5)

Measure a clip, optionally through a filter chain.

Supplying `--vf` makes it a **post-effect** measurement, which is the one
that governs a resolver’s answer — and the two are deliberately not
comparable.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.cli.motion(keyframes, , output=None, fps=None)

Compile a camera path into an ffmpeg fragment. RULE G’s compile half.

Each keyframe is `T:X,Y,W,H` — a time in seconds and a normalised,
top-left window, which is burns’ convention. Which filter comes out is not
an option here because it is not a matter of taste: a path that changes the
window’s SIZE compiles to `zoompan` (`crop` structurally cannot), and
everything else compiles to `crop`.

`--output` and `--fps` are needed only for a zoom, and `--fps` must be
the SOURCE’s rate: zoompan’s own default silently restamps the clip.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.cli.place(source, target, , mode='fit', backdrop='000000')

The ffmpeg chain that puts a WxH source into a WxH target.

`target` may be a size (`1920x1080`) or a preset name (`shorts`).

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.cli.terms(provider)

What is recorded about a provider’s licence, and what tier it projects to.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.cli.unverified()

What the licence ledger could NOT verify.

Printed rather than buried, because an unverified claim asserted as fact is
worse than no claim.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)
