# looks.cache

A `.cube` is a build artifact. This is where it gets built, once.

A 33-cube is ~950 KB; the spec that determines it is ~566 bytes of JSON. So a
Look carries the **spec** and a cache carries the **file**, addressed by a hash
of everything that determines its bytes. Two Looks with the same ramp share one
file; a changed ramp cannot reuse a stale one; and nothing that reaches the
bytes is allowed to bypass the address.

Generating rather than downloading is measured, not assumed: 33³ takes 0.141 s
with nothing but the standard library, which beats a network read and needs no
registry, no credentials and no availability.

### Atomicity is the whole difficulty

This package exists to be fanned out — one process per cut, several at once, all
of them wanting the same LUT. Two of them will race, and the loser must not be
able to hand ffmpeg a half-written file. \*\*A half-written `.cube` is not an
error, it is a silently wrong picture\*\*: ffmpeg reads what is there and
interpolates the rest of the lattice from nothing.

So a write is `mkstemp` in the destination directory plus [`os.replace()`](https://docs.python.org/3/library/os.html#os.replace).
A deterministic `<key>.tmp` path is **not** good enough — two writers would
open the same temp file and interleave into it, which is the race in a costume
rather than a fix.

`os.replace` is atomic on both POSIX and Windows, but it is not equally
*total*: \*\*Windows refuses the rename when the destination is open by anyone
else\*\*, where POSIX rename succeeds and leaves the reader on the old inode.
Under the fan-out this package is built for that is a live race, and it made
the Windows leg FLAKY rather than red — which is worse, because a flake gets
re-run rather than read. `_publish()` treats a lost race as the success it
is: the name is a hash of the content, so a writer that lost lost to bytes
identical to its own.

### What is deliberately absent

No eviction, no size cap, no TTL. A content-addressed store where every entry is
reproducible from its key does not need one: deleting the whole directory is
always safe and always correct, which is a stronger property than any policy
would give. [`sweep()`](#looks.cache.sweep) exists for a caller who wants that, and says so.

### Module Attributes

| [`DFLT_CACHE_ENV`](#looks.cache.DFLT_CACHE_ENV)   | Where cubes land when a caller names no directory.                          |
|-------------------------------------------------------------------|-----------------------------------------------------------------------------|
| [`CUBE_SUFFIX`](#looks.cache.CUBE_SUFFIX)      | The extension every entry carries.                                          |
| [`PENDING`](#looks.cache.PENDING)          | The payload key a step uses to say "I need a cube that does not exist yet". |

### Functions

| [`cache_dir`](#looks.cache.cache_dir)([into])                         | Where cubes are kept, resolved in one place.                              |
|--------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| [`cube_file`](#looks.cache.cube_file)(spec, \*[, size, title, into])  | Ensure the cube for `spec` exists on disk, and say where.                 |
| [`entries`](#looks.cache.entries)([into])                           | Every cube in the cache.                                                  |
| [`materialize`](#looks.cache.materialize)(plan, \*[, into])             | Build every artifact this plan asks for, and return a plan that has them. |
| [`materialize_many`](#looks.cache.materialize_many)(specs, \*[, size, into]) | Materialise several specs into one directory.                             |
| [`pending`](#looks.cache.pending)(plan)                             | The cube addresses this plan needs and has not been given.                |
| [`sweep`](#looks.cache.sweep)([into, keep])                       | Delete cached cubes, optionally keeping a set of keys.                    |

### Classes

| [`Materialised`](#looks.cache.Materialised)(path, key, hit)   | One cube on disk, and whether this call is what put it there.   |
|---------------------------------------------------------------------------------|-----------------------------------------------------------------|

### Exceptions

| [`CacheError`](#looks.cache.CacheError)   | The cache could not produce a usable file.   |
|---------------------------------------------------------------|----------------------------------------------|

### looks.cache.CUBE_SUFFIX *= '.cube'*

The extension every entry carries. Part of the filename rather than the key,
so a directory listing is readable and `lut3d=file=` gets what it expects.

### *exception* looks.cache.CacheError

Bases: [`LutError`](looks.lut.html.md#looks.lut.LutError)

The cache could not produce a usable file.

### looks.cache.DFLT_CACHE_ENV *= 'LOOKS_CACHE_DIR'*

Where cubes land when a caller names no directory. Under the user’s cache
dir rather than the package or the working directory, because a build
artifact belongs to the machine, not to the source tree or to whatever
directory a process happened to start in.

### *class* looks.cache.Materialised(path, key, hit)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One cube on disk, and whether this call is what put it there.

`hit` is reported rather than inferred because it is the only way a caller
can tell a cache that is working from one that is silently regenerating —
the file is identical either way, and only the clock differs.

### looks.cache.PENDING *= 'cube_request'*

The payload key a step uses to say “I need a cube that does not exist yet”.
A REQUEST, not a path: `compile_look` writes no files, so a compiled plan
names the artifact it wants and [`materialize()`](#looks.cache.materialize) is what supplies it.

### looks.cache.cache_dir(into=None)

Where cubes are kept, resolved in one place.

`into` wins, then `$LOOKS_CACHE_DIR`, then the platform cache directory.
The directory is created if absent — a cache that refuses to exist is not a
cache.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### looks.cache.cube_file(spec, , size=33, title='looks_gradient_map', into=None)

Ensure the cube for `spec` exists on disk, and say where.

Idempotent and safe to call concurrently. The second caller finds the file
the first one wrote; a caller racing another mid-write finds either the
complete previous file or the complete new one, never a partial.

* **Parameters:**
  * **size** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – The lattice size. Part of the address — a 17-cube and a 33-cube of
    one ramp are different files.
  * **title** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Written into the file’s first line, and therefore into the
    address. See [`looks.lut.cube_key()`](looks.lut.html.md#looks.lut.cube_key).
  * **into** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path), [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – The cache directory. Defaults to [`cache_dir()`](#looks.cache.cache_dir).
* **Return type:**
  [`Materialised`](#looks.cache.Materialised)

### Examples

```pycon
>>> import tempfile
>>> from looks import Ramp
>>> ramp = Ramp.from_hex([(8.2, '#2E0C18'), (100.0, '#FEF0DC')])
>>> with tempfile.TemporaryDirectory() as tmp:
...     first = cube_file(ramp, size=9, into=tmp)
...     again = cube_file(ramp, size=9, into=tmp)
...     (first.hit, again.hit, first.path == again.path)
(False, True, True)
```

It is a path-like, so it goes straight into a filter string:

```pycon
>>> import os
>>> with tempfile.TemporaryDirectory() as tmp:
...     cube = cube_file(ramp, size=9, into=tmp)
...     os.fspath(cube).endswith('.cube')
True
```

### looks.cache.entries(into=None)

Every cube in the cache. Partial writes in flight are not listed.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/typing.html#typing.Iterator)[[`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)]

### looks.cache.materialize(plan, , into=None)

Build every artifact this plan asks for, and return a plan that has them.

The split this preserves is the reason it is a separate verb rather than
part of compiling: **\`compile_look\` starts no process and writes no file**,
so a plan is pure data that can be hashed, stored, diffed and sent
somewhere else. Artifacts are what a plan needs to actually *run*, and
acquiring them is a side effect with a directory, a disk and a race in it.

Returns a new plan — the input is left alone, because a caller may well
want to keep the portable one.

Idempotent: a plan with nothing pending is returned unchanged, and running
it twice writes nothing the second time.

### Examples

A plan is built here by hand rather than by [`looks.compile_look()`](looks.html.md#looks.compile_look),
so this example needs no ffmpeg — the point is the verb, and a doctest
that needs a binary is a doctest that does not run in CI.

```pycon
>>> import tempfile
>>> from looks.licence import Tier, terms_for
>>> from looks.spec import ImplRef, LookPlan, Step
>>> impl = ImplRef(effect='gradient_map', backend='ffmpeg',
...                impl='gradient_map.ffmpeg.lut3d',
...                terms=terms_for('ffmpeg')[0])
>>> request = {'stops': [[8.2, '#2E0C18'], [100.0, '#FEF0DC']],
...            'size': 9, 'title': 'demo', 'contrast': 1.0, 'lift': 0.0,
...            'key': 'unused', 'filter_template': 'lut3d=file={file}'}
>>> plan = LookPlan(steps=(Step(effect='gradient_map', impl=impl,
...     tier=Tier.COPYLEFT_TOOL, payload={PENDING: request}),))
>>> len(pending(plan))                      # not built yet
1
>>> with tempfile.TemporaryDirectory() as tmp:
...     ready = materialize(plan, into=tmp)
...     pending(ready) == ()
True
>>> ready.steps[0].payload['filter'].startswith('lut3d=file=')
True
```

### looks.cache.materialize_many(specs, , size=33, into=None)

Materialise several specs into one directory.

Deduplicates by address on the way, so a set of Looks sharing a ramp
generates its cube once rather than once per Look.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Materialised`](#looks.cache.Materialised), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.cache.pending(plan)

The cube addresses this plan needs and has not been given.

Empty means the plan is ready to run. This is the question a caller should
ask before handing a plan to a backend, and it is what
[`looks.ffmpeg.vf()`](looks.ffmpeg.html.md#looks.ffmpeg.vf) answers with a refusal rather than a guess.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.cache.sweep(into=None, , keep=None)

Delete cached cubes, optionally keeping a set of keys. Returns what went.

There is no eviction policy and this is not one — it is the caller’s own
decision, made explicit. Every entry is reproducible from its key, so
deleting all of them is always safe; the only cost is regenerating, at
0.141 s per 33-cube.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]
