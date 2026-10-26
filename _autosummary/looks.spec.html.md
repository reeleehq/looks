# looks.spec

What a stylization *is*, before anything runs. Pure data, no I/O, no registry.

Five types carry the design, and one small one carries the hard part.

- [`Effect`](#looks.spec.Effect) — one named operation the caller **asks for**. It never says
  which implementation will serve it, and **it carries no licence tier**.
- [`Look`](#looks.spec.Look) — an ordered stack of Effects plus a [`Policy`](looks.licence.html.md#looks.licence.Policy).
  The authoring artifact; the thing you persist, diff and ship.
- [`ImplRef`](#looks.spec.ImplRef) — what an implementation **declares about itself**, including
  its [`Terms`](looks.licence.html.md#looks.licence.Terms). Not a tier: a tier is derived.
- [`Step`](#looks.spec.Step) and [`LookPlan`](#looks.spec.LookPlan) — the compiled form. A tier appears here
  for the first time, **read** off the selected implementation against a
  resolved environment.
- [`Ref`](#looks.spec.Ref) — a parameter that cannot be known until the clip is measured.

\*\*The load-bearing decision: `Effect` has no tier field.\*\* If a caller could
write `Effect(..., tier=PERMISSIVE)`, the refusal is theatre — the party who
wants the answer to be yes would be asserting it. The tier belongs to the
implementation and the environment, so it can only appear at compile time, which
is also the only moment anything decides what will actually run.

\*\*A `Ref` is pure data, never a callable.\*\* A callable would be evaluated during
resolution, so the *plan* would stay serialisable — but the **Look** is the
artifact, and a Look you cannot write to disk is a local variable, not an asset.
It also destroys diffability (two Looks print `<function <lambda> at 0x...>`)
and any honest cache key.

**The cost unit is CPU-seconds, not dollars**, with `falaw`’s
unknown-is-not-zero arithmetic transposed for its reasons: a sum must be total
to compose, and a headline ratio a human acts on must not fabricate.

Nothing here consults a registry, probes an environment, or opens a file. A Look
authored against a newer plugin set must still load, print and diff in a process
that lacks it — the discipline that lets an old build read a newer document.

```pycon
>>> look = Look(
...     name="que_calor",
...     steps=(
...         Effect(name="flatten", params={"scale": Ref("flatten_scale")}),
...         Effect(name="lut3d", params={"cube": "que_calor.cube"}),
...         Effect(name="posterize", params={"levels": 18}),
...     ),
... )
>>> look.is_resolved
False
>>> resolve(look, {"flatten_scale": 0.75})[0].params["scale"]
0.75
```

### Module Attributes

| [`LOOK_SCHEMA`](#looks.spec.LOOK_SCHEMA)   | Schema tags.                                                            |
|----------------------------------------------------------------|-------------------------------------------------------------------------|
| [`REF_MARKER`](#looks.spec.REF_MARKER)    | The reserved key that marks a deferred parameter in serialised form.    |
| [`EMPTY`](#looks.spec.EMPTY)         | An empty, immutable mapping — the default for every mapping field here. |

### Functions

| [`look_from_dict`](#looks.spec.look_from_dict)(d)                                  | Rebuild a Look.                                                                             |
|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------------|
| [`look_hash`](#looks.spec.look_hash)(look)                                    | Structural identity of the authored **intent**.                                             |
| [`look_to_dict`](#looks.spec.look_to_dict)(look)                                 | A JSON-able form of a Look, carrying its schema tag.                                        |
| [`output_key`](#looks.spec.output_key)(plan, source_digest)                    | The content-addressed key of what this plan makes from these bytes.                         |
| [`plan_from_dict`](#looks.spec.plan_from_dict)(d, \*, impls)                       | Rebuild a plan, given the implementations its steps name.                                   |
| [`plan_hash`](#looks.spec.plan_hash)(plan)                                    | Identity of the compiled pipeline — *will this produce the same pixels?*                    |
| [`plan_to_dict`](#looks.spec.plan_to_dict)(plan)                                 | A JSON-able form of a plan, carrying its schema tag.                                        |
| [`resolve`](#looks.spec.resolve)(look[, probe])                             | Replace every [`Ref`](#looks.spec.Ref) from one clip's `probe`. |
| [`resolve_across`](#looks.spec.resolve_across)(look, probes)                       | One resolved Look per probe — N in, N out.                                                  |
| [`select_impl`](#looks.spec.select_impl)(effect, candidates, \*[, policy, ...]) | Choose an implementation for `effect`, or raise saying why not.                             |

### Classes

| [`ClipSpec`](#looks.spec.ClipSpec)(\*, width, height, fps[, ...])            | The clip a plan is compiled **against**.                                   |
|-----------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| [`Effect`](#looks.spec.Effect)(\*, name[, params, at, impl, backend, ...]) | One named operation the caller asks for.                                   |
| [`ImplRef`](#looks.spec.ImplRef)(\*, effect, impl, backend, terms[, ...])   | What an implementation declares about itself — **terms, never a tier**.    |
| [`Look`](#looks.spec.Look)(\*[, steps, name, policy, order, ...])        | An ordered stack of Effects plus a policy.                                 |
| [`LookPlan`](#looks.spec.LookPlan)(\*[, steps, clip, env, look_name, ...])   | The compiled pipeline: what will run, against which clip and which binary. |
| [`Ref`](#looks.spec.Ref)(key[, default])                                | A parameter that cannot be known until the clip is measured.               |
| [`Span`](#looks.spec.Span)([start, end])                                 | Seconds, relative to frame 0 **as the host's decoder will see it**.        |
| [`Step`](#looks.spec.Step)(\*, effect, impl, tier[, params, at, ...])    | One compiled operation.                                                    |
| [`Target`](#looks.spec.Target)(\*values)                                   | What a Look's parameters resolve **against** — RULE N.                     |

### Exceptions

| [`SchemaError`](#looks.spec.SchemaError)         | A serialised document this build cannot read.                                                              |
|----------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| [`SpanUnsupported`](#looks.spec.SpanUnsupported)     | An `Effect.at` given to an implementation that cannot be gated.                                            |
| [`SpecError`](#looks.spec.SpecError)           | A Look or a plan that cannot mean what it says.                                                            |
| [`UnresolvedParameter`](#looks.spec.UnresolvedParameter) | A [`Ref`](#looks.spec.Ref) the probe did not answer, and which has no default. |

### *class* looks.spec.ClipSpec(, width, height, fps, duration_s=None, pix_fmt=None, color_range=None, color_space=None, sar=None, origin_s=None, color_assumed=False)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The clip a plan is compiled **against**. Not a file, not bytes.

The colour fields are not decoration; without them the plan’s central
promise is false. Measured on an untagged full-range source against a
correctly-tagged reference, the max channel error is 27/255 fixing
**neither** range nor matrix, **19** fixing range only, **20** fixing matrix
only, and **2** fixing both. Two independent unknowns, and half a fix is
barely a fix — so two clips identical in geometry but differing in colour
produce visibly different pixels through the same LUT, and a
[`plan_hash()`](#looks.spec.plan_hash) that omits them is lying.

`sar` is here because `xfade` silently tolerates a sample-aspect
mismatch and stamps its output 1:1 — the false-permission direction, in a
package built on refusal.

`None` means **not declared**, which is a third value and never a synonym
for a default.

### Examples

```pycon
>>> c = ClipSpec(width=1920, height=1080, fps=30.0)
>>> c.color_range is None            # untagged is a THIRD value
True
>>> c.aspect
1.7777777777777777
>>> ClipSpec(width=0, height=1080, fps=30.0)
Traceback (most recent call last):
...
looks.spec.SpecError: a ClipSpec needs positive dimensions, got 0x1080
```

#### *property* aspect *: [float](https://docs.python.org/3/builtins/functions.html#float)*

Display aspect, honouring `sar` when it is declared.

#### color_assumed *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

`color_space` was **assumed** by the caller (rule 22’s escape), not
read from the file. It is part of the plan’s identity: a plan built on a
guess must not hash like one built on a probe.

#### *property* colour_is_declared *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Whether both colour unknowns are answered.

Read this before trusting a colour operation: half the tags is barely
better than none.

### Examples

```pycon
>>> ClipSpec(width=2, height=2, fps=1.0).colour_is_declared
False
>>> ClipSpec(width=2, height=2, fps=1.0, color_range="limited",
...          color_space="bt709").colour_is_declared
True
```

#### origin_s *: [Optional](https://docs.python.org/3/library/typing.html#typing.Optional)[[float](https://docs.python.org/3/builtins/functions.html#float)]*

The filter-timeline time of this part’s frame 0, as the host’s decoder
will see it. **\`None\` means undeclared, and undeclared is not 0.**

Measured (rule 28): an INPUT-side `-ss` rebases the filter timeline to
0, an OUTPUT-side one does not. So what a [`Span`](#looks.spec.Span) of “4 s to 5 s”
selects is a property of *the host’s seek style*, not of the clip — and
assuming 0 for a host that seeks on the output side puts the right look
on the wrong frames, with no error anywhere. `muvid` seeks input-side, so
0 is correct for the first consumer and wrong in general, which is
exactly why it must be said rather than defaulted.

### looks.spec.EMPTY *: [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Any](https://docs.python.org/3/library/typing.html#typing.Any)]* *= {}*

An empty, immutable mapping — the default for every mapping field here.

A shared frozen singleton rather than `field(default_factory=dict)`:
`frozen=True` prevents *rebinding* a field, not mutating the dict behind
it, so a mutable default lets [`look_hash()`](#looks.spec.look_hash) change after a Look has been
built, hashed and stored — and makes the objects unhashable despite the
decorator generating `__hash__`.

### *class* looks.spec.Effect(, name, params=FrozenMap(), at=None, impl=None, backend=None, metadata=FrozenMap())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One named operation the caller asks for. Pure data; no tier, no impl.

`name` is the **capability** (`"flatten"`, `"posterize"`), never an
implementation. `impl` and `backend` pin *which* answer serves
it — and neither bypasses the ceiling: a pinned implementation above the
policy is still refused, because a pin says which one you want, not that you
may have it.

`metadata` is identity-free labelling and never enters
[`look_hash()`](#looks.spec.look_hash).

### Examples

```pycon
>>> e = Effect(name="posterize", params={"levels": 18})
>>> e.name, e.params["levels"]
('posterize', 18)
>>> e.is_resolved
True
>>> Effect(name="flatten", params={"scale": Ref("s")}).is_resolved
False
>>> Effect(name="")
Traceback (most recent call last):
...
looks.spec.SpecError: an Effect needs a capability name
```

#### *property* is_resolved *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Whether every parameter is concrete.

#### *property* refs *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[Ref](#looks.spec.Ref), ...]*

Every deferred parameter, in no particular order.

#### resolved(probe)

A copy with every [`Ref`](#looks.spec.Ref) replaced, or raise.

* **Return type:**
  [`Effect`](#looks.spec.Effect)

### *class* looks.spec.ImplRef(, effect, impl, backend, terms, requires_filters=(), impl_version='1', timeline=True, time_varying=None, rgb_only=None, preference=0)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What an implementation declares about itself — **terms, never a tier**.

A tier is a position on a policy ladder; terms are what was observed. An
implementation that could declare its own tier could declare itself
acceptable, which is the same failure as an `Effect` carrying one.

#### effect

The capability served.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### impl

`"<effect>.<backend>.<variant>"`, globally unique.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### backend

`"ffmpeg"` | `"frame"` | `"external"`.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### terms

What it is. See [`looks.licence.Terms`](looks.licence.html.md#looks.licence.Terms).

* **Type:**
  [`Terms`](looks.licence.html.md#looks.licence.Terms)

#### requires_filters

ffmpeg filters this implementation emits.

* **Type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

#### impl_version

A behaviour lock, not a receipt — “same interface,
changed behaviour” bumps it, and it enters [`plan_hash()`](#looks.spec.plan_hash)
**unconditionally**.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### timeline

Whether it can be gated to an `Effect.at`. Answers a
different question from [`time_varying`](#looks.spec.ImplRef.time_varying) and the two are close
to inverses in practice: `motion.ffmpeg.crop` compiles to
`zoompan`/`crop` expressions that read `in_time` and has
**no** timeline support (`timeline=False`), while every static
grade has timeline support (`timeline=True`) and never reads the
clock. See issue #17.

* **Type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

#### time_varying

Whether this implementation’s own fragment reads the
clock **regardless of any span** — true only for a camera move
whose expressions reference `in_time`. Distinct from
[`Step.time_varying`](#looks.spec.Step.time_varying), which also accounts for an
`Effect.at` Span gating an otherwise-static filter with
`enable='between(t,...)'`.

\*\*Tri-state, and `None` is not `False`.\*\* The same rule as
`Step.cpu_seconds` and
[`can_flicker`](looks.frame_dependency.html.md#looks.frame_dependency.DependencyReport.can_flicker):
“we were not told” and “it does not” are different claims, and only
one of them is a guarantee a caller may act on. An implementation
registered without declaring this reads as **unknown**, never as
“does not read the clock” — a silent `False` here is exactly the
false permission that would let muvid#73’s ramp restart ship
unwarned. [`looks.ffmpeg.register_defaults()`](looks.ffmpeg.html.md#looks.ffmpeg.register_defaults) requires every
built-in implementation to declare it explicitly for this reason.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`bool`](https://docs.python.org/3/builtins/functions.html#bool)]

#### rgb_only

Whether the implementation has a step that only takes RGB,
so the backend converts the picture to RGB and back around it
(rule 22: on such a step the clip’s colour space must be declared
or assumed, because the converter’s own guess shifts luma on
ffmpeg 6.1). Declared on the implementation so the backend-agnostic
compiler asks one flag instead of knowing any backend’s filter
list. **Tri-state:** `None` is undeclared. For an
`ffmpeg` implementation `EffectRegistry.register()` settles
it from `requires_filters` (and refuses `False` on an RGB-only
filter), so rule 22 never sees `None` there; a `frame`
implementation is always `True` (the pipe hands it RGB frames; it
may not declare `False`); for another backend `None` is not
asserted, and only `True` triggers rule 22.
Changing it changes the backend’s pixels: bump `impl_version`.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`bool`](https://docs.python.org/3/builtins/functions.html#bool)]

#### preference

Explicit tiebreak within one tier; lower wins.

* **Type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

### Examples

```pycon
>>> from looks.licence import terms_for
>>> impl = ImplRef(effect="lut3d", impl="lut3d.ffmpeg.default",
...                backend="ffmpeg", terms=terms_for("ffmpeg")[0],
...                requires_filters=("lut3d",))
>>> impl.impl_version
'1'
>>> impl.timeline
True
>>> impl.time_varying is None      # undeclared is unknown, not False
True
>>> impl.rgb_only is None
True
```

#### *property* tier *: [Optional](https://docs.python.org/3/library/typing.html#typing.Optional)[[Tier](looks.licence.html.md#looks.licence.Tier)]*

The rung its terms project onto, or `None` when off the ladder.

Derived on read, never stored — so it cannot drift from the terms.

### looks.spec.LOOK_SCHEMA *= 'looks.look/v1'*

Schema tags. Two kinds, two independent lifecycles — which is exactly why a
future migration registry must be keyed on `(kind, from_version)` and never
on `(from, to)`. `an` paid for that with an#77: two kinds at the same
version number, and the wrong migration silently running against the wrong
document.

### *class* looks.spec.Look(\*, steps=(), name='', policy=Policy(max_tier=<Tier.COPYLEFT_TOOL: 'copyleft_tool'>, allow_field_restricted=frozenset(), order=(<Tier.PURE: 'pure'>, <Tier.PERMISSIVE: 'permissive'>, <Tier.WEAK_COPYLEFT: 'weak_copyleft'>, <Tier.COPYLEFT_TOOL: 'copyleft_tool'>, <Tier.COPYLEFT_SHIPPED: 'copyleft_shipped'>)), target=Target.EXTERNAL, metadata=FrozenMap(), version=1)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

An ordered stack of Effects plus a policy. The artifact you ship.

`a + b` concatenates the steps and takes the **stricter** of the two
policies, never the looser — a guarantee composition can silently relax is
not a guarantee. Widening is always a separate deliberate act
([`with_policy()`](#looks.spec.Look.with_policy)).

`policy` is **not** part of [`look_hash()`](#looks.spec.look_hash): a ceiling changes what
a Look is *allowed* to compile to, never what it asks for.

### Examples

```pycon
>>> from looks.licence import Policy, Tier
>>> safe = Look(name="grade", steps=(Effect(name="gamma"),),
...             policy=Policy(max_tier=Tier.PERMISSIVE))
>>> lab = Look(steps=(Effect(name="flatten"),))
>>> (safe + lab).policy.max_tier          # the STRICTER survives
<Tier.PERMISSIVE: 'permissive'>
>>> len((safe + lab).steps)
2
>>> (safe + lab).with_policy(lab.policy).policy.max_tier
<Tier.COPYLEFT_TOOL: 'copyleft_tool'>
```

#### *property* is_resolved *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Whether the whole Look is concrete.

#### *property* refs *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[Ref](#looks.spec.Ref), ...]*

Every deferred parameter across every step.

#### with_policy(policy)

A copy under a different ceiling — the deliberate widening act.

* **Return type:**
  [`Look`](#looks.spec.Look)

### *class* looks.spec.LookPlan(\*, steps=(), clip=None, env=None, look_name='', policy=Policy(max_tier=<Tier.COPYLEFT_TOOL: 'copyleft_tool'>, allow_field_restricted=frozenset(), order=(<Tier.PURE: 'pure'>, <Tier.PERMISSIVE: 'permissive'>, <Tier.WEAK_COPYLEFT: 'weak_copyleft'>, <Tier.COPYLEFT_TOOL: 'copyleft_tool'>, <Tier.COPYLEFT_SHIPPED: 'copyleft_shipped'>)), probe=FrozenMap(), metadata=FrozenMap(), version=1)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The compiled pipeline: what will run, against which clip and which binary.

The **env fingerprint belongs here and not on the Look**. A `Look` is
portable data; a `LookPlan` is compiled against one binary whose filter
set and licence are part of what determines the pixels — so it says which
one, and that enters [`plan_hash()`](#looks.spec.plan_hash). Folding the environment in does not
break portability, because the portable artifact is the Look.

**The plan holds no live callables.** A plan with a closure in it cannot be
serialised, diffed or hashed, which is the entire reason this shape was
adopted. The callable is resolved from the registry at execution time, by
the runner.

Deliberately not modelled: peak memory and streaming shape. Those are the
executor’s invariant, and a plan claiming to predict them is an invitation
to write the `looks.render()` this package is chartered to stay out of.

### Examples

```pycon
>>> plan = LookPlan()
>>> plan.total_cpu_seconds
0.0
>>> plan.has_unknown_costs
False
>>> plan.realtime_factor is None     # no clip to divide by
True
```

#### *property* has_unknown_costs *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Whether anything is unpriced. A gate reads this, not the sum.

#### *property* known_cpu_seconds *: [float](https://docs.python.org/3/builtins/functions.html#float)*

The priced part only — the honest half of the pair.

#### *property* realtime_factor *: [Optional](https://docs.python.org/3/library/typing.html#typing.Optional)[[float](https://docs.python.org/3/builtins/functions.html#float)]*

CPU-seconds per second of output, or `None` when anything is unknown.

The asymmetry against [`total_cpu_seconds`](#looks.spec.LookPlan.total_cpu_seconds) is deliberate: a sum
must be total to compose, but a headline ratio a human acts on must not
fabricate. Returning `0.0` for “we did not know” is reelee#208’s
failure mode, where a `$0.00`-because-unknown read as “under the
threshold, spend freely”.

#### *property* time_varying *: [Optional](https://docs.python.org/3/library/typing.html#typing.Optional)[[bool](https://docs.python.org/3/builtins/functions.html#bool)]*

Whether any compiled step reads the clock — see [`Step.time_varying`](#looks.spec.Step.time_varying).

The question issue #17 was filed for: a consumer that renders a blend
as a separate input-seeked invocation (input-side `-ss` rebases the
filter clock to 0) needs to know, per compiled fragment, whether that
rebasing can affect it. `not impl.timeline` answers a different
question and gets it wrong on three of the four filters that matter —
this property is the one to ask instead.

\*\*Tri-state, and a known `True` wins over an unknown step.\*\* One
step that certainly reads the clock makes the plan `True` even if
another step’s implementation never declared itself — a plan is not
“unknown” about the one thing it is sure of. Absent any certain
`True`, an unknown step poisons the answer to `None`: “every step
we could classify does not read the clock” is not “nothing here
reads the clock”, the same asymmetry [`has_unknown_costs`](#looks.spec.LookPlan.has_unknown_costs) keeps
separate from [`total_cpu_seconds`](#looks.spec.LookPlan.total_cpu_seconds).

#### *property* total_cpu_seconds *: [float](https://docs.python.org/3/builtins/functions.html#float)*

Sum with unknown coerced to `0.0` — a documented **lower bound**.

Total so sums compose. Read it beside [`unknown_step_count`](#looks.spec.LookPlan.unknown_step_count), never
alone: the true cost is this *plus an unknown amount* spread over that
many steps.

#### *property* unknown_step_count *: [int](https://docs.python.org/3/builtins/functions.html#int)*

How many steps carry no cost at all.

### looks.spec.REF_MARKER *= '$ref'*

The reserved key that marks a deferred parameter in serialised form.

Documented cost: a parameter whose legitimate value is a mapping containing
this exact key is inexpressible. The decoder is strict about the shape, so
the ambiguity raises rather than being hit silently.

### *class* looks.spec.Ref(key, default=<object object>)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A parameter that cannot be known until the clip is measured.

Serialised as `{"$ref": "flatten_scale", "default": 0.5}`. Per-parameter
on purpose: a diff shows exactly which knobs are clip-dependent, and a Ref
with no default that the probe does not answer **raises**.

Rejected alternative — a per-clip `variants` table. It is JSON-native and
would work, but it cannot express the design’s central rule (\*this parameter
must be measured, and there is no global fallback\*), because a missing entry
is either a `KeyError` or a silent fall-through to the base.

### Examples

```pycon
>>> Ref("flatten_scale").has_default
False
>>> Ref("flatten_scale", 0.5).has_default
True
```

#### *property* has_default *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Whether absence from the probe is tolerable.

#### resolve(probe, , where='')

The value for this Ref, or raise.

### Examples

```pycon
>>> Ref("s", 0.5).resolve({})
0.5
>>> Ref("s").resolve({}, where="flatten.scale")
Traceback (most recent call last):
...
looks.spec.UnresolvedParameter: flatten.scale needs 's'...
```

* **Return type:**
  [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)

### *exception* looks.spec.SchemaError

Bases: [`SpecError`](#looks.spec.SpecError)

A serialised document this build cannot read.

### *class* looks.spec.Span(start=None, end=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Seconds, relative to frame 0 **as the host’s decoder will see it**.

Says *where a look applies*. It never says where a cut is — that is the
caller’s, and the distinction is what keeps this package out of the EDL.

### Examples

```pycon
>>> Span(1.0, 3.5).duration
2.5
>>> Span(None, None).is_whole
True
>>> Span(3.0, 1.0)
Traceback (most recent call last):
...
looks.spec.SpecError: a Span must not end before it starts: 3.0 -> 1.0
```

#### *property* duration *: [Optional](https://docs.python.org/3/library/typing.html#typing.Optional)[[float](https://docs.python.org/3/builtins/functions.html#float)]*

Length in seconds, or `None` when either end is open.

#### *property* is_whole *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

Whether this span covers everything (both ends open).

### *exception* looks.spec.SpanUnsupported

Bases: [`SpecError`](#looks.spec.SpecError)

An `Effect.at` given to an implementation that cannot be gated.

### *exception* looks.spec.SpecError

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

A Look or a plan that cannot mean what it says.

### *class* looks.spec.Step(, effect, impl, tier, params=FrozenMap(), at=None, payload=FrozenMap(), cpu_seconds=None, metadata=FrozenMap())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One compiled operation. A tier appears here, read and not asserted.

`payload` is backend-shaped and the asymmetry is deliberate: an
`ffmpeg` payload is fully inspectable (read a stored plan and see the
exact filtergraph), while `frame` and `external` payloads are only
*nameable*.

\*\*A payload names a registry key, never a `module:attr` import path.\*\* A
plan is a document, documents arrive from places, and a document that can
name `os:system` is a remote-code-execution primitive wearing a schema
tag.

`cpu_seconds` is `None` for unknown, **never zero**.

### Examples

```pycon
>>> from looks.licence import terms_for
>>> impl = ImplRef(effect="lut3d", impl="lut3d.ffmpeg.default",
...                backend="ffmpeg", terms=terms_for("ffmpeg")[0])
>>> from looks.licence import Tier
>>> s = Step(effect="lut3d", impl=impl, tier=Tier.WEAK_COPYLEFT,
...          payload={"filter": "lut3d=look.cube"})
>>> s.payload["filter"]
'lut3d=look.cube'
>>> s.cpu_seconds is None            # unknown, not free
True
```

An impl that declares it does not read the clock stays that way — gate
it to a span and it does, regardless (issue #17, the question
`ImplRef.timeline` looks like but is not):

```pycon
>>> from dataclasses import replace
>>> static = replace(s, impl=replace(impl, time_varying=False))
>>> static.time_varying
False
>>> replace(static, at=Span(1.0, 2.0)).time_varying
True
```

An impl that never declared it reads as **unknown**, not `False`:

```pycon
>>> s.time_varying is None
True
```

#### *property* time_varying *: [Optional](https://docs.python.org/3/library/typing.html#typing.Optional)[[bool](https://docs.python.org/3/builtins/functions.html#bool)]*

Whether this compiled fragment reads the clock (issue #17).

Not `not self.impl.timeline` — that field means “can be gated to a
span”, which is close to the *inverse* of this question: the one
genuinely clock-reading implementation registered today
(`motion.ffmpeg.crop`, whose `zoompan`/`crop` expressions
reference `in_time`) has **no** timeline support, while every static
grade has it and never reads the clock.

**Tri-state.** A span that actually bounds something is a *certain*
`True` regardless of what the implementation declares — it compiles
with `enable='between(t,...)'` no matter what — using the same
predicate [`looks.ffmpeg.gated()`](looks.ffmpeg.html.md#looks.ffmpeg.gated) uses to decide whether to emit
one ([`Span.is_whole`](#looks.spec.Span.is_whole), so the two never drift apart). Absent
that, the answer is exactly [`ImplRef.time_varying`](#looks.spec.ImplRef.time_varying), unknown
included: an implementation that never declared it does not become
“does not read the clock” just because no span was given either.

### *class* looks.spec.Target(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

What a Look’s parameters resolve **against** — RULE N.

- `EXTERNAL` — a fixed target outside the material: a delivery
  contract, a reference palette, a colour conform. One clip’s probe answers
  it, and [`resolve()`](#looks.spec.resolve) serves it.
- `SET_RELATIVE` — the target *is the set’s own distribution*. The
  answer for one clip depends on every other clip, so only
  [`resolve_across()`](#looks.spec.resolve_across) can serve it and [`resolve()`](#looks.spec.resolve) **raises**.

That refusal is the measured lesson as a type: normalising the OUTPUT across
sources is not a thing you can compute from one clip.

The field is `target` and **not** `intent="style"|"grade"`: a colour
conform is a *normalisation* whose target is external and fixed, and under a
style/grade wording it would have to be mislabelled.

### *exception* looks.spec.UnresolvedParameter

Bases: [`SpecError`](#looks.spec.SpecError)

A [`Ref`](#looks.spec.Ref) the probe did not answer, and which has no default.

Deliberately a refusal rather than a fallback. The measured lesson: one
global flattening scale made the softest of three sources softer still
(46 -> 38, against 35 -> 72 and 117 -> 114), so it became the softest thing
on screen. A silent global fallback is exactly that mistake, re-armed.

### looks.spec.look_from_dict(d)

Rebuild a Look. An unrecognised tag is refused; a missing one is v1.

### Examples

```pycon
>>> look = Look(name="x", steps=(Effect(name="lut3d", params={"a": Ref("r")}),))
>>> back = look_from_dict(look_to_dict(look))
>>> back.steps[0].params["a"]
Ref(key='r', default=<object object at ...>)
>>> look_from_dict({"schema": "looks.look/v9"})
Traceback (most recent call last):
...
looks.spec.SchemaError: this build reads 'looks.look/v1'...
```

* **Return type:**
  [`Look`](#looks.spec.Look)

### looks.spec.look_hash(look)

Structural identity of the authored **intent**.

Registry-independent, environment-independent, **policy-independent**.
`metadata` is excluded (labelling, not identity) and so is `policy`: a
ceiling changes what a Look may compile to, never what it asks for.

### Examples

```pycon
>>> from looks.licence import Policy, Tier
>>> a = Look(name="x", steps=(Effect(name="gamma", params={"g": 1.1}),))
>>> look_hash(a) == look_hash(replace(a, name="y"))       # name IS identity
False
>>> look_hash(a) == look_hash(replace(a, metadata={"who": "thor"}))
True
>>> look_hash(a) == look_hash(a.with_policy(Policy(max_tier=Tier.PURE)))
True
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.spec.look_to_dict(look)

A JSON-able form of a Look, carrying its schema tag.

### Examples

```pycon
>>> d = look_to_dict(Look(name="x", steps=(Effect(name="lut3d"),)))
>>> d["schema"], d["name"]
('looks.look/v1', 'x')
```

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### looks.spec.output_key(plan, source_digest)

The content-addressed key of what this plan makes from these bytes.

`source_digest` is a digest of the source’s **content**, never its path or
its URL. That signature is `falaw`’s D1 defect stated as a type: keying on
upstream *URLs* made a byte-identical regeneration miss the cache.

`looks` computes the formula and **refuses to open the file**, because
reading bytes is execution.

### Examples

```pycon
>>> k = output_key(LookPlan(), "a" * 64)
>>> len(k)
64
>>> k == output_key(LookPlan(), "b" * 64)
False
>>> output_key(LookPlan(), "/path/to/clip.mp4")
Traceback (most recent call last):
...
looks.spec.SpecError: source_digest must be a content digest...
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.spec.plan_from_dict(d, , impls)

Rebuild a plan, given the implementations its steps name.

**\`\`impls\`\` is required, and a step naming one that is absent raises.** A
serialised step carries its implementation’s *key*, not its
[`Terms`](looks.licence.html.md#looks.licence.Terms) — and reconstructing an `ImplRef` from a key
alone would mean inventing the terms, which is inventing a licence verdict.
In a package whose thesis is that unknown refuses, a plan that rehydrates
into a confident tier nobody observed is the worst possible artifact.

So the caller supplies the registry it trusts, and a plan built against
implementations this process does not have is a refusal rather than a guess.
That is also what makes a stored plan safe to receive from elsewhere: it
cannot name its way into a capability the receiving process did not already
install.

* **Raises:**
  [**SchemaError**](#looks.spec.SchemaError) – An unrecognised schema tag, or a step naming an
      implementation `impls` does not carry.
* **Return type:**
  [`LookPlan`](#looks.spec.LookPlan)

### Examples

```pycon
>>> from looks.licence import terms_for, Tier
>>> impl = ImplRef(effect="lut3d", impl="lut3d.ffmpeg.default",
...                backend="ffmpeg", terms=terms_for("ffmpeg")[0])
>>> plan = LookPlan(steps=(Step(effect="lut3d", impl=impl,
...                             tier=Tier.WEAK_COPYLEFT,
...                             payload={"filter": "lut3d=x.cube"}),))
>>> back = plan_from_dict(plan_to_dict(plan), impls={impl.impl: impl})
>>> plan_hash(back) == plan_hash(plan)
True
```

A plan naming an implementation this process lacks is refused, not
approximated:

```pycon
>>> plan_from_dict(plan_to_dict(plan), impls={})
Traceback (most recent call last):
...
looks.spec.SchemaError: this plan names implementations this process
does not have: ['lut3d.ffmpeg.default']...
```

### looks.spec.plan_hash(plan)

Identity of the compiled pipeline — *will this produce the same pixels?*

Folds, per step: the implementation key **and its version**, the resolved
parameters, the span and the compiled payload; plus the clip’s geometry
**and its colour state**, and the environment fingerprint.

`impl_version` folds in **unconditionally**. `nw` and `falaw` omit
theirs when it equals its default; that is a *migration device* protecting
an installed base of cache keys, and `looks` has no installed base. Do not
copy the sentinel.

### Examples

```pycon
>>> plan_hash(LookPlan()) == plan_hash(LookPlan())
True
>>> a = LookPlan(clip=ClipSpec(width=2, height=2, fps=1.0))
>>> b = LookPlan(clip=ClipSpec(width=2, height=2, fps=1.0,
...                            color_range="full"))
>>> plan_hash(a) == plan_hash(b)      # colour state is identity
False
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.spec.plan_to_dict(plan)

A JSON-able form of a plan, carrying its schema tag.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### looks.spec.resolve(look, probe={})

Replace every [`Ref`](#looks.spec.Ref) from one clip’s `probe`.

The **identity** on a Look holding no Refs, so a caller who already has
numbers never meets this function.

* **Raises:**
  * [**SpecError**](#looks.spec.SpecError) – The Look is `SET_RELATIVE` — RULE N. Its target is the
        set’s own distribution, which one clip cannot supply.
  * [**UnresolvedParameter**](#looks.spec.UnresolvedParameter) – A Ref with no default that `probe` does not
        answer.
* **Return type:**
  [`Look`](#looks.spec.Look)

### Examples

```pycon
>>> look = Look(steps=(Effect(name="flatten", params={"scale": Ref("s")}),))
>>> resolve(look, {"s": 0.75})[0].params["scale"]
0.75
>>> resolve(Look(steps=(Effect(name="lut3d"),)))     # identity
Look(steps=(Effect(name='lut3d', ...),), ...)
```

A set-relative Look refuses the single-clip resolver:

```pycon
>>> resolve(Look(target=Target.SET_RELATIVE), {})
Traceback (most recent call last):
...
looks.spec.SpecError: this Look is SET_RELATIVE...
```

### looks.spec.resolve_across(look, probes)

One resolved Look per probe — N in, N out.

The resolver for a target that is the set’s own distribution. This function
does **not** compute the cross-clip answer: it applies per-clip probes a
caller has already solved for, because choosing them requires running the
effect, and running things is not this package’s job. See
[`looks.measure`](looks.html.md#looks.measure) for the measurement half.

### Examples

```pycon
>>> look = Look(target=Target.SET_RELATIVE,
...             steps=(Effect(name="flatten", params={"scale": Ref("s")}),))
>>> got = resolve_across(look, [{"s": 0.5}, {"s": 0.5}, {"s": 0.75}])
>>> [lk[0].params["scale"] for lk in got]
[0.5, 0.5, 0.75]
```

Each result is EXTERNAL: the set-relative question has been answered,
and re-resolving would ask it again against a different set.

```pycon
>>> got[0].target
<Target.EXTERNAL: 'external'>
>>> resolve_across(look, [])
Traceback (most recent call last):
...
looks.spec.SpecError: resolve_across needs at least one probe...
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Look`](#looks.spec.Look), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.spec.select_impl(effect, candidates, \*, policy=Policy(max_tier=<Tier.COPYLEFT_TOOL: 'copyleft_tool'>, allow_field_restricted=frozenset(), order=(<Tier.PURE: 'pure'>, <Tier.PERMISSIVE: 'permissive'>, <Tier.WEAK_COPYLEFT: 'weak_copyleft'>, <Tier.COPYLEFT_TOOL: 'copyleft_tool'>, <Tier.COPYLEFT_SHIPPED: 'copyleft_shipped'>)), available_filters=None)

Choose an implementation for `effect`, or raise saying why not.

In order: honour an explicit `impl` or `backend` pin, drop anything the
environment cannot run, drop anything the policy refuses, drop anything that
cannot be gated when the effect has a span, then take the lowest tier and
break ties on [`ImplRef.preference`](#looks.spec.ImplRef.preference).

**A pin narrows, it never permits.** A pinned implementation the policy
refuses is still refused — otherwise the pin is a way to assert a tier,
which is the thing [`Effect`](#looks.spec.Effect) deliberately cannot do.

* **Raises:**
  * [**SpecError**](#looks.spec.SpecError) – Nothing survived, with the reason.
  * [**SpanUnsupported**](#looks.spec.SpanUnsupported) – Every survivor refuses a span the effect carries.
* **Return type:**
  [`ImplRef`](#looks.spec.ImplRef)

### Examples

```pycon
>>> from looks.licence import terms_for, Policy, Tier
>>> ff = terms_for("ffmpeg")[0]
>>> cands = [ImplRef(effect="blur", impl="blur.ffmpeg.gblur",
...                  backend="ffmpeg", terms=ff, requires_filters=("gblur",))]
>>> select_impl(Effect(name="blur"), cands).impl
'blur.ffmpeg.gblur'
```

A filter this build lacks removes the candidate:

```pycon
>>> select_impl(Effect(name="blur"), cands,
...             available_filters=frozenset({"scale"}))
Traceback (most recent call last):
...
looks.spec.SpecError: no implementation of 'blur' survived...
```
