# looks.compile

A Look plus a clip plus a binary, compiled into a plan — and re-checked.

[`compile_look()`](#looks.compile.compile_look) is the join: a portable `Look` (what was asked for) meets
a `ClipSpec` (what it is being applied to) and an `FfmpegEnv` (what this
machine can actually do), and the result is a `LookPlan` — a document saying
what will run, at which tier, against which binary.

### An ffmpeg step’s tier belongs to the binary, so the binary is required

An `ImplRef` declares `terms` — what was observed about the implementation.
For an **ffmpeg-backed** implementation that declaration cannot be the whole
answer, because there is not one ffmpeg on a machine: measured here, `PATH`
is 8.1 / GPL-3 / 481 filters while `imageio-ffmpeg`’s bundled binary is 7.1 /
GPL-2 / 484, and the filter sets are non-nested. The same registered
implementation is a different licence position on each.

So the compiler **substitutes the probed binary’s terms** into every ffmpeg
candidate before selection, and selection, the step’s tier, and a later
[`audit()`](#looks.compile.audit) all read that one substituted value. The consequence is that
`env` is **required** for an ffmpeg step: without it the tier is unknown, and
unknown is a refusal rather than a default.

What this deliberately does *not* do is raise a step’s tier because it uses a
GPL-gated filter. [`looks.licence`](looks.licence.html.md#module-looks.licence) settles that —  *“a GPL-gated filter does
not raise the tier; the binary already has it”* — and the mechanism that keeps
an `eq` look off an LGPL build is simpler and stronger: on such a build `eq`
is not compiled in at all, so it is absent from `env.filters` and selection
drops the candidate. A licence ceiling and a missing capability are different
refusals, and [`unmet_filters()`](#looks.compile.unmet_filters) keeps them apart.

### Why [`audit()`](#looks.compile.audit) exists, and why it re-derives instead of reading

A `LookPlan` is data, so it travels: written to a file, sent across a process
boundary, stored in a graph, replayed a week later. Every one of those is a gap
in which the thing that vouched for it stopped being present.

So a plan carries both its [`Policy`](looks.licence.html.md#looks.licence.Policy) (the ceiling it was
compiled under) and, on each step, a `tier`. \*\*The audit trusts neither of
them about the step’s actual position.\*\* It goes back to the implementation’s
`terms` — what was *observed* about the licence — and re-derives the tier from
those. A plan whose stored tier disagrees with what its terms classify to is not
a plan with a stale field; it is a plan asserting a position it is not entitled
to, and it is refused by name.

That is the same argument that keeps a tier off `Effect` and off `ImplRef`:
anything that can declare its own tier can declare itself acceptable. A stored
plan is just the version of that with a filesystem in between.

The audit also refuses a plan naming an implementation this process does not
have, or one whose `impl_version` has moved. Both mean the same thing — the
plan describes behaviour this build does not implement — and guessing a
substitute is exactly the failure the version lock exists to prevent.

### Module Attributes

| [`EFFECT_PARAM_CHECKS`](#looks.compile.EFFECT_PARAM_CHECKS)   | What an effect's parameters must satisfy, keyed by EFFECT — never by implementation.   |
|------------------------------------------------------------------------|----------------------------------------------------------------------------------------|

### Functions

| [`audit`](#looks.compile.audit)(plan, \*[, policy, registry])              | Re-check a plan against its own declared ceiling.                |
|---------------------------------------------------------------------------------------------------|------------------------------------------------------------------|
| [`check_effect_params`](#looks.compile.check_effect_params)(effect)                      | Refuse parameters no implementation of this effect could honour. |
| [`compile_all`](#looks.compile.compile_all)(looks_, \*\*kwargs)                  | Compile several Looks under one set of arguments.                |
| [`compile_look`](#looks.compile.compile_look)(look, \*[, clip, env, policy, ...]) | Compile a Look into a plan.                                      |
| [`describe`](#looks.compile.describe)(plan)                                   | A plan as a few lines of text — for a CLI, a log, or a review.   |
| [`payloads`](#looks.compile.payloads)(plan[, backend])                        | Every step's payload, optionally for one backend.                |
| [`unmet_filters`](#looks.compile.unmet_filters)(plan, env)                         | Filters this plan needs that this binary does not have.          |

### Exceptions

| [`CompileError`](#looks.compile.CompileError)   | A Look that cannot be compiled against this clip and this binary.   |
|-----------------------------------------------------------------|---------------------------------------------------------------------|
| [`PlanRefused`](#looks.compile.PlanRefused)    | A stored plan that may not be run as it stands.                     |

### *exception* looks.compile.CompileError

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

A Look that cannot be compiled against this clip and this binary.

### looks.compile.EFFECT_PARAM_CHECKS *= {'colorbalance': <function \_check_colorbalance>, 'contrast': <function \_check_contrast>, 'curves': <function \_check_curves>, 'gate_weave': <function \_check_gate_weave>, 'grain': <function \_check_grain>, 'halation': <function \_check_halation>, 'vignette': <function \_check_vignette>}*

What an effect’s parameters must satisfy, keyed by EFFECT — never by
implementation. A check that lives inside one compiler is a check the
licence tier can switch off: `contrast` with `amount=-1` was refused on the
LGPL path and emitted `eq=contrast=-1.0` on the GPL one, so the same Look was
valid or invalid depending on how the binary was built. Rule 29b says the
tier must not decide what the viewer sees; it must not decide whether the
document is accepted either.

### *exception* looks.compile.PlanRefused

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

A stored plan that may not be run as it stands. Never a warning.

### looks.compile.audit(plan, , policy=None, registry=None)

Re-check a plan against its own declared ceiling. Raises, or returns None.

Call this on any plan that crossed a boundary — read from a file, received
over a wire, replayed from a graph. It answers one question: \*may this run
here, now, as it stands?\*

Nothing the plan says about its own position is believed. Each step’s tier
is re-derived from the implementation’s `terms` and compared to what the
step claims; a disagreement is a refusal naming the step, not a field to
refresh.

* **Parameters:**
  * **policy** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Policy`](looks.licence.html.md#looks.licence.Policy)]) – The ceiling to check against. Defaults to the plan’s own —
    which is the right default and the weaker check, since a plan
    carrying a permissive policy vouches for itself. Pass your own to
    ask whether it may run under *your* ceiling.
  * **registry** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`EffectRegistry`](looks.registry.html.md#looks.registry.EffectRegistry)]) – Which implementations exist here.
* **Raises:**
  * [**PlanRefused**](#looks.compile.PlanRefused) – If a step names an implementation this process lacks, or
        one whose `impl_version` has moved, or one whose stored tier
        disagrees with its terms.
  * [**LooksLicenceError**](looks.licence.html.md#looks.licence.LooksLicenceError) – If a step exceeds the ceiling.
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### looks.compile.check_effect_params(effect)

Refuse parameters no implementation of this effect could honour.

Called before an implementation is chosen, so every implementation of an
effect accepts exactly the same documents.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### looks.compile.compile_all(looks_, \*\*kwargs)

Compile several Looks under one set of arguments.

A convenience with one real property: it compiles **all or none**. A
partially-compiled batch invites a caller to run the half that worked,
which for a set-relative Look is precisely the mistake `resolve_across`
exists to prevent.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`LookPlan`](looks.spec.html.md#looks.spec.LookPlan), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.compile.compile_look(look, , clip=None, env=None, policy=None, probe={}, registry=None)

Compile a Look into a plan. No process is started and no file is written.

* **Parameters:**
  * **look** ([`Look`](looks.spec.html.md#looks.spec.Look)) – What was asked for. Portable data.
  * **clip** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`ClipSpec`](looks.spec.html.md#looks.spec.ClipSpec)]) – What it is being applied to. Needed by any effect whose answer
    depends on the frame — its absence is only an error if an effect
    asks for it.
  * **env** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`FfmpegEnv`](looks.environment.html.md#looks.environment.FfmpegEnv)]) – Which binary. When given, an implementation whose filters this
    build lacks is dropped from selection rather than discovered at
    run time.
  * **policy** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Policy`](looks.licence.html.md#looks.licence.Policy)]) – The ceiling. Defaults to the Look’s own.
  * **probe** ([`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]) – Measurements that [`Ref`](looks.spec.html.md#looks.spec.Ref) parameters resolve
    against.
  * **registry** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`EffectRegistry`](looks.registry.html.md#looks.registry.EffectRegistry)]) – Which implementations exist. Defaults to
    [`looks.registry.REGISTRY`](looks.registry.html.md#looks.registry.REGISTRY).
* **Return type:**
  [`LookPlan`](looks.spec.html.md#looks.spec.LookPlan)
* **Returns:**
  A [`LookPlan`](looks.spec.html.md#looks.spec.LookPlan) holding no live callables — the runner
  resolves each step’s code from the registry by key.
* **Raises:**
  * [**CompileError**](#looks.compile.CompileError) – If an effect has no admissible implementation. The
        message says which constraint emptied the pool, because “no
        implementation available” alone is the least useful refusal in the
        package.
  * [**LooksLicenceError**](looks.licence.html.md#looks.licence.LooksLicenceError) – If the selected implementation exceeds
        the ceiling. Selection already filters by policy, so this fires
        only when nothing admissible existed.

### looks.compile.describe(plan)

A plan as a few lines of text — for a CLI, a log, or a review.

Deliberately not a round-trippable format. Serialisation is
[`looks.spec.plan_to_dict()`](looks.spec.html.md#looks.spec.plan_to_dict)’s job, and a second one would be a second
thing to keep in sync.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.compile.payloads(plan, backend=None)

Every step’s payload, optionally for one backend.

The reading surface for a stored plan: an `ffmpeg` payload is fully
inspectable, so this is how a caller sees the exact filtergraph a plan
stands for without running anything.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.compile.unmet_filters(plan, env)

Filters this plan needs that this binary does not have.

Separate from [`audit()`](#looks.compile.audit) on purpose: a licence refusal is about what a
caller may do, and a missing filter is about what a machine can do. They
fail for different reasons, are fixed by different people, and collapsing
them produces a message that helps neither.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]
