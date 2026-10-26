# looks

A facade over video stylization: named effects carrying a licence tier.

Named effects that compile to a backend command, each carrying a licence tier,
so a caller can demand commercial-safe-only and get a **refusal** rather than a
surprise. Pure-data specs, separable from execution — the `falaw.Plan` shape,
except the cost unit is CPU-seconds rather than dollars.

The one call that shows what this is for:

```default
>>> from looks import needs_gpl
>>> needs_gpl(['scale', 'eq', 'lut3d'])
('eq',)
```

`eq` is the obvious brightness/contrast/gamma filter, and it exists \*\*only in
a GPL build of ffmpeg\*\*. Nothing in the ffmpeg CLI will tell you, because the
binary on your machine runs it fine — and `curves` / `colorlevels` /
`exposure` do the same job in an LGPL one.

**Zero dependencies.** ffmpeg is shelled out to, never linked.

This namespace is **curated**: it carries the surface a caller uses, not
everything the package defines. Reach into a submodule for the rest —
[`looks.spec`](looks.spec.html.md#module-looks.spec), [`looks.environment`](looks.environment.html.md#module-looks.environment), [`looks.licence`](looks.licence.html.md#module-looks.licence),
[`looks.geometry`](looks.geometry.html.md#module-looks.geometry), [`looks.lut`](looks.lut.html.md#module-looks.lut), [`looks.measure`](#looks.measure),
[`looks.frame_dependency`](looks.frame_dependency.html.md#module-looks.frame_dependency).

One rename happens at this boundary and nowhere else: `frame_dependency`’s
`classify` is exported as [`classify_dependency()`](#looks.classify_dependency), because
`licence.classify` has the better claim to the bare name here — a caller
reaching for `looks.classify` wants the licence question. Inside the
submodule it keeps its own short name.

Two names are deliberately absent, and a test asserts it: there is no
`render` and no `apply`. Every ffmpeg process this package starts ends in
`-f null -` — it emits the chain, and the caller runs it. See
`looks._run`.

### Functions

| [`probe`](#looks.probe)([ffmpeg, timeout])                           | Interrogate one ffmpeg binary.                                                                                                                         |
|-----------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`needs_gpl`](#looks.needs_gpl)(filters, \*[, known])                    | Which of `filters` exist only in a GPL build, in the order given.                                                                                      |
| [`known_filters`](#looks.known_filters)()                                    | Every filter name FFmpeg n8.1 declares — the universe [`needs_gpl()`](#looks.needs_gpl) checks against.                     |
| [`gpl_only_filters`](#looks.gpl_only_filters)()                                 | Filter names FFmpeg gates behind `--enable-gpl`.                                                                                                       |
| [`terms_for`](#looks.terms_for)(provider[, realisation, component])      | Every ledger row matching a provider, optionally narrowed.                                                                                             |
| [`ffmpeg_terms`](#looks.ffmpeg_terms)(env, \*[, realisation, today])        | One probed ffmpeg binary, as [`Terms`](#looks.Terms).                                                                   |
| [`classify`](#looks.classify)(terms, \*[, today])                       | Locate `terms` in the axis space.                                                                                                                      |
| [`assess`](#looks.assess)(terms, \*[, order, today])                  | Assess a provider made of several components: **the worst one wins.**                                                                                  |
| [`assess_ffmpeg_chain`](#looks.assess_ffmpeg_chain)(filters, \*, env[, ...])       | The licence position of a filter chain on one probed binary.                                                                                           |
| [`check`](#looks.check)(assessment, policy, subject, \*[, ...])      | Raise unless `policy` admits `assessment`.                                                                                                             |
| [`unverified_claims`](#looks.unverified_claims)()                                | What the research explicitly did **not** establish.                                                                                                    |
| [`resolve`](#looks.resolve)(look[, probe])                             | Replace every [`Ref`](#looks.Ref) from one clip's `probe`.                                                            |
| [`resolve_across`](#looks.resolve_across)(look, probes)                       | One resolved Look per probe — N in, N out.                                                                                                             |
| [`select_impl`](#looks.select_impl)(effect, candidates, \*[, policy, ...]) | Choose an implementation for `effect`, or raise saying why not.                                                                                        |
| [`look_to_dict`](#looks.look_to_dict)(look)                                 | A JSON-able form of a Look, carrying its schema tag.                                                                                                   |
| [`look_from_dict`](#looks.look_from_dict)(d)                                  | Rebuild a Look.                                                                                                                                        |
| [`plan_to_dict`](#looks.plan_to_dict)(plan)                                 | A JSON-able form of a plan, carrying its schema tag.                                                                                                   |
| [`plan_from_dict`](#looks.plan_from_dict)(d, \*, impls)                       | Rebuild a plan, given the implementations its steps name.                                                                                              |
| [`look_hash`](#looks.look_hash)(look)                                    | Structural identity of the authored **intent**.                                                                                                        |
| [`plan_hash`](#looks.plan_hash)(plan)                                    | Identity of the compiled pipeline — *will this produce the same pixels?*                                                                               |
| [`output_key`](#looks.output_key)(plan, source_digest)                    | The content-addressed key of what this plan makes from these bytes.                                                                                    |
| [`placement`](#looks.placement)(source, target, \*[, mode, rounding])    | The full geometric answer for one clip.                                                                                                                |
| [`reframe`](#looks.reframe)(source, target, \*[, mode, backdrop, ...]) | [`placement()`](#looks.placement) plus a backdrop.                                                                          |
| [`scaled_size`](#looks.scaled_size)(source, target, \*[, mode, rounding])  | The size the source is scaled to, before any crop or pad.                                                                                              |
| [`ffmpeg_chain`](#looks.ffmpeg_chain)(placement, \*[, backdrop])            | The resolved `scale,crop,pad` chain for one placement.                                                                                                 |
| [`snap_even`](#looks.snap_even)(size)                                    | Both axes rounded **down** to even — the yuv420p requirement.                                                                                          |
| [`social_size`](#looks.social_size)(name)                                  | Resolve a `SOCIAL_SIZES` preset name.                                                                                                                  |
| [`register_effect`](#looks.register_effect)(impl, compiler, \*\*kwargs)        | Register into `REGISTRY`.                                                                                                                              |
| [`effects`](#looks.effects)()                                          | Every effect `REGISTRY` can serve.                                                                                                                     |
| [`compile_look`](#looks.compile_look)(look, \*[, clip, env, policy, ...])   | Compile a Look into a plan.                                                                                                                            |
| [`audit`](#looks.audit)(plan, \*[, policy, registry])                | Re-check a plan against its own declared ceiling.                                                                                                      |
| [`describe`](#looks.describe)(plan)                                     | A plan as a few lines of text — for a CLI, a log, or a review.                                                                                         |
| [`payloads`](#looks.payloads)(plan[, backend])                          | Every step's payload, optionally for one backend.                                                                                                      |
| [`unmet_filters`](#looks.unmet_filters)(plan, env)                           | Filters this plan needs that this binary does not have.                                                                                                |
| [`blended_frames`](#looks.blended_frames)(transition, fps, \*[, offset])      | How many frames will be a mixture of the two shots.                                                                                                    |
| [`is_hard_cut`](#looks.is_hard_cut)(transition, fps, \*[, offset])         | Will this transition produce no blended frame at all?                                                                                                  |
| [`check_visible`](#looks.check_visible)(transition, fps, \*[, offset])       | Raise unless the transition will actually be seen.                                                                                                     |
| [`xfade_options`](#looks.xfade_options)(transition, \*, offset[, fps, ...])  | The `xfade` options for this transition — options, not a filter.                                                                                       |
| [`solve_across`](#looks.solve_across)(candidates, \*[, statistic, ...])     | One parameter value per clip, so the set's measurements sit close together.                                                                            |
| [`probes_for`](#looks.probes_for)(spread, parameter)                      | A [`Spread`](#looks.Spread) as the probes [`looks.resolve_across()`](#looks.resolve_across) takes. |
| [`pipe_plan`](#looks.pipe_plan)(plan, \*, source[, clip, pix_fmt])       | Arrange a compiled plan as processes — emitted as data, never started.                                                                                 |
| [`runs`](#looks.runs)(plan)                                         | Maximal runs of consecutive steps sharing a backend.                                                                                                   |
| [`materialize`](#looks.materialize)(plan, \*[, into])                      | Build every artifact this plan asks for, and return a plan that has them.                                                                              |
| [`cube_file`](#looks.cube_file)(spec, \*[, size, title, into])           | Ensure the cube for `spec` exists on disk, and say where.                                                                                              |
| [`pending`](#looks.pending)(plan)                                      | The cube addresses this plan needs and has not been given.                                                                                             |
| [`cache_dir`](#looks.cache_dir)([into])                                  | Where cubes are kept, resolved in one place.                                                                                                           |
| [`sweep`](#looks.sweep)([into, keep])                                | Delete cached cubes, optionally keeping a set of keys.                                                                                                 |
| [`vf`](#looks.vf)(plan, \*[, gate])                               | A whole plan as one `-vf` fragment: input-index-free, splice-ready.                                                                                    |
| [`filter_string`](#looks.filter_string)(name[, options])                     | One filter, with its options escaped.                                                                                                                  |
| [`escape_filter_value`](#looks.escape_filter_value)(value)                         | Escape a value for use as a filter option inside a filtergraph.                                                                                        |
| [`register_defaults`](#looks.register_defaults)([registry])                      | Register the built-in ffmpeg effects.                                                                                                                  |
| [`compile_motion`](#looks.compile_motion)(keyframes, \*[, output, fps, ...])  | A camera path to an ffmpeg fragment, filter chosen by what the path does.                                                                              |
| [`crop_fragment`](#looks.crop_fragment)(keyframes)                           | A path of constant window size, compiled to `crop`.                                                                                                    |
| [`zoompan_fragment`](#looks.zoompan_fragment)(keyframes, \*, output, fps)       | A path whose window size varies, compiled to `zoompan`.                                                                                                |
| [`reframe_motion`](#looks.reframe_motion)(keyframes, \*[, aspect_tolerance])  | Split a path into a static reframing crop and a path relative to it.                                                                                   |
| [`is_source_shaped`](#looks.is_source_shaped)(keyframes)                        | Is every window geometrically similar to the whole frame?                                                                                              |
| [`gradient_map`](#looks.gradient_map)(ramp, \*[, accent, contrast, lift])   | Build a [`GradientMap`](#looks.GradientMap), warning about a ramp that reaches black.                                         |
| [`cube_text`](#looks.cube_text)(spec, \*[, size, title])                 | Render an Iridas `.cube` for `spec`, as text.                                                                                                          |
| [`cube_key`](#looks.cube_key)(spec, \*[, size, title])                  | A content hash of everything that determines the file's bytes.                                                                                         |
| [`write_cube`](#looks.write_cube)(spec, path, \*[, size, title])          | Write the `.cube` for `spec` to `path` and return it.                                                                                                  |
| [`measure`](#looks.measure)(source, \*[, source_id, vf, frames, ...])  | Measure one clip, at the source or through a Look's compiled chain.                                                                                    |
| [`compare`](#looks.compare)(a, b)                                      | Raise [`Incomparable`](#looks.Incomparable) unless `a` and `b` can be compared.                                                |
| [`dispersion`](#looks.dispersion)(stats, \*[, key])                       | The max/min ratio of `key` across `stats` — the quantity to minimise.                                                                                  |
| [`color_range`](#looks.color_range)(source, \*[, ffprobe, timeout])        | What range `source` **declares**, with `untagged` as a real answer.                                                                                    |
| [`classify_dependency`](#looks.classify_dependency)(chain, \*[, ffprobe, timeout]) | Measure what `chain` depends on.                                                                                                                       |
| [`assert_flicker_free`](#looks.assert_flicker_free)(chain, \*\*kwargs)             | Raise unless `chain` provably cannot flicker.                                                                                                          |

### Classes

| [`FfmpegEnv`](#looks.FfmpegEnv)([path, version, licence, filters, ...])   | One machine's ffmpeg, as far as it can be determined without running it.                                         |
|------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| [`Licence`](#looks.Licence)(\*values)                                   | What licence an ffmpeg build carries, as `ffmpeg -L` reports it.                                                 |
| [`Terms`](#looks.Terms)(\*, provider, realisation, spdx, coupling)    | What one component declares about itself.                                                                        |
| [`Coupling`](#looks.Coupling)(\*values)                                  | How the implementation is reached — whether copyleft can touch us.                                               |
| [`Reach`](#looks.Reach)(\*values)                                     | How far the implementation's copyleft extends.                                                                   |
| [`Conveyance`](#looks.Conveyance)(\*values)                                | Whether a *declared dependency closure* ships the implementation.                                                |
| [`FieldOfUse`](#looks.FieldOfUse)(\*values)                                | Whether the *purpose* is permitted.                                                                              |
| [`Tier`](#looks.Tier)(\*values)                                      | A rung on a ladder that is **policy, not fact**.                                                                 |
| [`Verdict`](#looks.Verdict)(\*values)                                   | Which region of the axis space the terms landed in.                                                              |
| [`Assessment`](#looks.Assessment)(\*, terms, tier, verdict[, ...])         | Where [`classify()`](#looks.classify) located some terms.                            |
| [`Policy`](#looks.Policy)(\*[, max_tier, ...])                         | A ceiling, plus the thing a ceiling deliberately cannot reach.                                                   |
| [`Effect`](#looks.Effect)(\*, name[, params, at, impl, backend, ...])  | One named operation the caller asks for.                                                                         |
| [`Look`](#looks.Look)(\*[, steps, name, policy, order, ...])         | An ordered stack of Effects plus a policy.                                                                       |
| [`Ref`](#looks.Ref)(key[, default])                                 | A parameter that cannot be known until the clip is measured.                                                     |
| [`Span`](#looks.Span)([start, end])                                  | Seconds, relative to frame 0 **as the host's decoder will see it**.                                              |
| [`ClipSpec`](#looks.ClipSpec)(\*, width, height, fps[, ...])             | The clip a plan is compiled **against**.                                                                         |
| [`Target`](#looks.Target)(\*values)                                    | What a Look's parameters resolve **against** — RULE N.                                                           |
| [`ImplRef`](#looks.ImplRef)(\*, effect, impl, backend, terms[, ...])    | What an implementation declares about itself — **terms, never a tier**.                                          |
| [`Step`](#looks.Step)(\*, effect, impl, tier[, params, at, ...])     | One compiled operation.                                                                                          |
| [`LookPlan`](#looks.LookPlan)(\*[, steps, clip, env, look_name, ...])    | The compiled pipeline: what will run, against which clip and which binary.                                       |
| [`Size`](#looks.Size)(width, height)                                 | A pixel size.                                                                                                    |
| [`Box`](#looks.Box)(x, y, width, height)                            | An axis-aligned pixel box, top-left origin, y downwards.                                                         |
| [`Placement`](#looks.Placement)(source, target, scale[, crop, ...])       | Scale the source to `scale`, take `crop` out, put it at `offset`.                                                |
| [`Reframe`](#looks.Reframe)(placement[, backdrop])                      | A placement plus what fills the part of the target it does not cover.                                            |
| [`Solid`](#looks.Solid)([rgb])                                        | A flat colour behind the placed frame.                                                                           |
| [`Blurred`](#looks.Blurred)([sigma, dim])                               | A blurred, dimmed copy of the source, scaled to cover — the "social" look.                                       |
| [`EffectRegistry`](#looks.EffectRegistry)([name])                              | Effect name to implementations, and implementation key to code.                                                  |
| [`Transition`](#looks.Transition)(duration_s[, curve])                     | How a shot blends in from its predecessor.                                                                       |
| [`Candidate`](#looks.Candidate)(value, stats)                             | One candidate parameter value, and what it measured.                                                             |
| [`Choice`](#looks.Choice)(source_id, value, statistic)                 | The value one clip was given, and the measurement that justifies it.                                             |
| [`Spread`](#looks.Spread)(choices, ratio, log_spread, ...[, ...])      | The answer: one choice per clip, and how consistent the set now is.                                              |
| [`PipePlan`](#looks.PipePlan)(segments, boundaries[, source])            | The whole arrangement, as data.                                                                                  |
| [`FrameSegment`](#looks.FrameSegment)(op, decode, encode, pix_fmt, ...)      | One ffmpeg → Python → ffmpeg segment.                                                                            |
| [`FilterSegment`](#looks.FilterSegment)(vf)                                   | A run of ffmpeg steps with no frame operation in it: one `-vf`.                                                  |
| [`Materialised`](#looks.Materialised)(path, key, hit)                        | One cube on disk, and whether this call is what put it there.                                                    |
| [`Window`](#looks.Window)(x, y, w, h)                                  | A concrete [`WindowLike`](#looks.WindowLike), for callers who do not already have one. |
| [`WindowLike`](#looks.WindowLike)(\*args, \*\*kwargs)                      | Burns' convention: normalised, top-left origin, window fractions.                                                |
| [`Keyframe`](#looks.Keyframe)(t, window)                                 | A window, at a time in seconds from the start of the clip.                                                       |
| [`Ramp`](#looks.Ramp)(stops)                                         | Colours ordered by lightness — the whole specification of a gradient map.                                        |
| [`Accent`](#looks.Accent)(ramp[, hue, hue_width, ...])                 | A second ramp for colours the main ramp should not flatten.                                                      |
| [`GradientMap`](#looks.GradientMap)(ramp[, accent, contrast, lift])         | A ramp, an optional accent, and the tone adjustment applied before both.                                         |
| [`ClipStats`](#looks.ClipStats)(source_id, stage, instrument, ...)        | What one source contributes to one stage of one pipeline, as measured.                                           |
| [`Dependency`](#looks.Dependency)(\*values)                                | What an effect's output depends on, worst case.                                                                  |
| [`DependencyReport`](#looks.DependencyReport)(dependency[, time_delta, ...])     | What the two probes measured, and what follows from it.                                                          |

### Exceptions

| [`UnknownFilter`](#looks.UnknownFilter)          | A filter name that is not in any known universe.                                                           |
|-------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------|
| [`LooksLicenceError`](#looks.LooksLicenceError)      | Base for every licence refusal.                                                                            |
| [`LicenceForbidden`](#looks.LicenceForbidden)       | Off the ladder, permanently.                                                                               |
| [`LicenceFieldRestricted`](#looks.LicenceFieldRestricted) | Non-commercial / research-only / no-derivatives.                                                           |
| [`LicenceCeilingExceeded`](#looks.LicenceCeilingExceeded) | On the ladder, above the ceiling.                                                                          |
| [`LicenceUnknown`](#looks.LicenceUnknown)         | Undeterminable, unprobeable, or self-contradictory.                                                        |
| [`SpecError`](#looks.SpecError)              | A Look or a plan that cannot mean what it says.                                                            |
| [`SchemaError`](#looks.SchemaError)            | A serialised document this build cannot read.                                                              |
| [`SpanUnsupported`](#looks.SpanUnsupported)        | An `Effect.at` given to an implementation that cannot be gated.                                            |
| [`UnresolvedParameter`](#looks.UnresolvedParameter)    | A [`Ref`](#looks.Ref) the probe did not answer, and which has no default. |
| [`GeometryError`](#looks.GeometryError)          | A size or mode that cannot produce a placement.                                                            |
| [`RegistryError`](#looks.RegistryError)          | A registration that would make a later refusal point at the wrong thing.                                   |
| [`ImplConflict`](#looks.ImplConflict)           | That key is taken.                                                                                         |
| [`UnknownImpl`](#looks.UnknownImpl)            | A plan names an implementation this process does not have.                                                 |
| [`CompileError`](#looks.CompileError)           | A Look that cannot be compiled against this clip and this binary.                                          |
| [`PlanRefused`](#looks.PlanRefused)            | A stored plan that may not be run as it stands.                                                            |
| [`TransitionError`](#looks.TransitionError)        | A transition that cannot be honoured as asked.                                                             |
| [`AcrossError`](#looks.AcrossError)            | A set-relative question that cannot be answered as asked.                                                  |
| [`PipeError`](#looks.PipeError)              | A plan that cannot be arranged as a pipe, or not safely.                                                   |
| [`CacheError`](#looks.CacheError)             | The cache could not produce a usable file.                                                                 |
| [`FfmpegBackendError`](#looks.FfmpegBackendError)     | A step that cannot be expressed as a filter fragment.                                                      |
| [`MotionError`](#looks.MotionError)            | A path that cannot be compiled, or that would compile to a lie.                                            |
| [`LutError`](#looks.LutError)               | A ramp or lattice that cannot produce a usable LUT.                                                        |
| [`MeasurementError`](#looks.MeasurementError)       | A measurement that could not be taken, or one that must not be compared.                                   |
| [`Incomparable`](#looks.Incomparable)           | Two measurements whose identity fields disagree.                                                           |

### *class* looks.Accent(ramp, hue=52.0, hue_width=14.0, min_saturation=0.42, saturation_soft=0.3, strength=0.7)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A second ramp for colours the main ramp should not flatten.

A pure gradient map erases every hue distinction. When the reference keeps
one — the first real look kept warm accents, 9.35% of pixels and every one
warm — a second ramp is blended in, weighted by how saturated the source
pixel is and how close its hue sits to [`hue`](#looks.Accent.hue).

#### ramp

The colours this accent maps to, indexed by lightness exactly as
the main ramp is.

* **Type:**
  [`Ramp`](looks.lut.html.md#looks.lut.Ramp)

#### hue

Centre of the hue band to rescue, in degrees.

* **Type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### hue_width

Gaussian sigma of the hue window, in degrees.

* **Type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### min_saturation

Below this saturation, weight is zero — an accent keyed
on hue alone would recolour every near-grey pixel whose hue is
numerically nearby but perceptually meaningless.

* **Type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### saturation_soft

Saturation range over which weight ramps from 0 to 1.

* **Type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### strength

Maximum blend weight, in `[0, 1]`.

* **Type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### weight(rgb)

Blend weight for one source colour, in `[0, strength]`.

### Examples

```pycon
>>> gold = Ramp.from_hex([(0.0, '#2A1206'), (100.0, '#FEF6DF')])
>>> a = Accent(ramp=gold)
>>> round(a.weight((0.95, 0.82, 0.15)), 3)      # a saturated amber
0.695
>>> a.weight((0.5, 0.5, 0.5))                   # grey: no hue to rescue
0.0
>>> a.weight((0.15, 0.30, 0.65))                # blue: outside the band
0.0
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### *exception* looks.AcrossError

Bases: [`MeasurementError`](#looks.MeasurementError)

A set-relative question that cannot be answered as asked.

### *class* looks.Assessment(, terms, tier, verdict, reasons=(), advisories=(), parts=())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Where [`classify()`](#looks.classify) located some terms. Not a permission.

`tier is None` means *no rung* — either an axis is unknown or the terms
are in the forbidden region. A `Verdict.FIELD_RESTRICTED` assessment
**still carries its rung**, and that is the fix for a real defect: with the
rung dropped, honouring a field-of-use opt-in left nothing for the ceiling
test to compare, so opting into a research model silently waived the
copyleft ceiling as well.

#### advisories *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), ...]*

live patents,
recorded conditions, stale evidence, an explicit reach override.

* **Type:**
  Things a caller must be told but which are not refusals

#### parts *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[Assessment](looks.licence.html.md#looks.licence.Assessment), ...]*

The per-component assessments when this came from [`assess()`](#looks.assess).
[`check()`](#looks.check) applies the ceiling to **every** part, so a composite
cannot admit something one of its components would not.

#### *property* severity *: [int](https://docs.python.org/3/builtins/functions.html#int)*

Rank in `_VERDICT_SEVERITY`; higher is louder.

### *class* looks.Blurred(sigma=15.0, dim=0.7)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A blurred, dimmed copy of the source, scaled to cover — the “social” look.

This is `mixing`’s `method="social"`, separated from the fit mode so that
the two compose. Its defaults reproduce that branch.

### Examples

```pycon
>>> Blurred().sigma, Blurred().dim
(15.0, 0.7)
```

### *class* looks.Box(x, y, width, height)

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

### *exception* looks.CacheError

Bases: [`LutError`](looks.lut.html.md#looks.lut.LutError)

The cache could not produce a usable file.

### *class* looks.Candidate(value, stats)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One candidate parameter value, and what it measured.

`value` is whatever the parameter is — a flattening scale, a sigma, a
level count. It is carried opaquely: this module compares *measurements*,
never parameters.

### *class* looks.Choice(source_id, value, statistic)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The value one clip was given, and the measurement that justifies it.

### *class* looks.ClipSpec(, width, height, fps, duration_s=None, pix_fmt=None, color_range=None, color_space=None, sar=None, origin_s=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The clip a plan is compiled **against**. Not a file, not bytes.

The colour fields are not decoration; without them the plan’s central
promise is false. Measured on an untagged full-range source against a
correctly-tagged reference, the max channel error is 27/255 fixing
**neither** range nor matrix, **19** fixing range only, **20** fixing matrix
only, and **2** fixing both. Two independent unknowns, and half a fix is
barely a fix — so two clips identical in geometry but differing in colour
produce visibly different pixels through the same LUT, and a
[`plan_hash()`](#looks.plan_hash) that omits them is lying.

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
0, an OUTPUT-side one does not. So what a [`Span`](#looks.Span) of “4 s to 5 s”
selects is a property of *the host’s seek style*, not of the clip — and
assuming 0 for a host that seeks on the output side puts the right look
on the wrong frames, with no error anywhere. `muvid` seeks input-side, so
0 is correct for the first consumer and wrong in general, which is
exactly why it must be said rather than defaulted.

### *class* looks.ClipStats(source_id, stage, instrument, luma_space, sample_spec, n_frames, sharpness=None, sharpness_unit='', sharpness_space='full_y', luma=None, saturation_mean=None, temporal_delta=None, blur=None, color_range='untagged', extra=dict())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What one source contributes to one stage of one pipeline, as measured.

The first five fields are the value’s **identity**, not decoration. Two
`ClipStats` are comparable only if `stage`, `instrument`,
`luma_space` and `sample_spec` all agree — [`compare()`](#looks.compare) raises
otherwise.

#### source_id

Whatever the caller calls this clip. Never a path, so a
measurement survives the file moving.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### stage

`source` or `post_effect`. See `Stage`.

* **Type:**
  [`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'source'`, `'post_effect'`]

#### instrument

What took the measurement, including its version.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### luma_space

See `LumaSpace`.

* **Type:**
  [`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'coded_y'`, `'full_y'`, `'bgr2gray'`, `'linear_y'`, `'lstar'`]

#### sample_spec

How the frames were chosen. Part of identity because the
sampler moves the answer: taking the median over the 3 widest spans
gave one clip a spatial-information figure of 30.7 where all 17
spans gave 41.9 — a 27% move from the sampler alone.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### n_frames

How many frames were actually measured.

* **Type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

#### sharpness

Higher is sharper, in the instrument’s own units.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### sharpness_unit

What those units are.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### sharpness_space

Which luma the sharpness was computed in — \*\*not
necessarily\*\* [`luma_space`](#looks.ClipStats.luma_space). `siti` works in full range,
`signalstats` in coded, and conflating them makes a 16% metadata
artefact look like a picture difference.

* **Type:**
  [`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'coded_y'`, `'full_y'`, `'bgr2gray'`, `'linear_y'`, `'lstar'`]

#### luma

The luma distribution.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[`LumaSummary`]

#### saturation_mean

Mean chroma magnitude.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### temporal_delta

Mean frame-to-frame change. The flicker check as one
number — the shipped look sits at 0.89-1.12x its own source’s.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### blur

`blurdetect`’s estimate. Higher is blurrier, the opposite
direction from [`sharpness`](#looks.ClipStats.sharpness), which is why they are separate
fields rather than one “quality” number.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### color_range

See `ColorRange`.

* **Type:**
  [`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'limited'`, `'full'`, `'untagged'`]

#### extra

Instrument-specific values nothing above has a home for.

* **Type:**
  [`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`float`](https://docs.python.org/3/builtins/functions.html#float)]

### Examples

```pycon
>>> s = ClipStats(source_id='c03', stage='post_effect',
...               instrument='ffmpeg-8.1/siti', luma_space='coded_y',
...               sample_spec='uniform:5', n_frames=5, sharpness=38.4)
>>> s.sharpness
38.4
>>> s.identity
('post_effect', 'ffmpeg-8.1/siti', 'coded_y', 'full_y', 'uniform:5')
```

#### *property* identity *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [str](https://docs.python.org/3/builtins/stdtypes.html#str), [str](https://docs.python.org/3/builtins/stdtypes.html#str), [str](https://docs.python.org/3/builtins/stdtypes.html#str), [str](https://docs.python.org/3/builtins/stdtypes.html#str)]*

The five fields two measurements must share to be comparable.

### *exception* looks.CompileError

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

A Look that cannot be compiled against this clip and this binary.

### *class* looks.Conveyance(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Whether a *declared dependency closure* ships the implementation.

Whose closure is the load-bearing word. A caller’s pre-existing
`imageio-ffmpeg` is `FINDS` — `looks` does not declare it and
does not convey it. It becomes `CONVEYS` for whoever *does* declare
it, which is why a ledger row is keyed on how you obtain the thing rather
than on the thing: `realisation="system"` finds, `realisation="pypi:x"`
describes the position of a package that declares `x`.

### *class* looks.Coupling(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How the implementation is reached — whether copyleft can touch us.

This axis and [`Conveyance`](#looks.Conveyance) are the two that separate the four cases
people habitually conflate: executing a copyleft program you found
(`SUBPROCESS` + `FINDS`), executing one you shipped (`+ CONVEYS`),
linking one (`IN_PROCESS`), and calling a hosted one (`SERVICE`).

### *class* looks.Dependency(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

What an effect’s output depends on, worst case.

Ordered by how badly each behaves across a cut:

- `INDEPENDENT` — the same input pixel gives the same output pixel,
  always. Cannot flicker. This is what the flagship look is.
- `INDEPENDENT` — no probe could make the effect touch a pixel it
  should not have. **Evidence, not proof** — see the module docstring.
  A pixel-local map and a small spatial filter both land here, and for the
  flicker question that is the right grouping: neither can flicker.
- `TIME_VARYING` — output depends on the frame index or clock.
  Deterministic and reproducible, but it changes: film grain is the wanted
  case.
- `CONTENT_ADAPTIVE` — output depends on the frame’s global
  statistics. **This flickers**, and it is the class the whole
  frame-independence argument is about.
- `TEMPORAL` — output at frame *n* depends on frames before it.
  Structurally incompatible with the execution model this package serves:
  the consumer renders one bounded ffmpeg **per cut**, so a temporal filter
  meets a hard discontinuity at every cut and produces an artefact at every
  one of them.
- `NONDETERMINISTIC` — two applications of the effect to the SAME
  input disagree. A reproducibility hazard rather than a flicker one: a
  re-render produces a different picture. Detected first, because it
  invalidates every other probe here.
- `UNDETERMINED` — a probe could not run. Never a synonym for
  independent.

### *class* looks.DependencyReport(dependency, time_delta=None, content_delta=None, temporal_delta=None, determinism_delta=None, note='')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What the two probes measured, and what follows from it.

#### dependency

The verdict.

* **Type:**
  [`Dependency`](looks.frame_dependency.html.md#looks.frame_dependency.Dependency)

#### time_delta

Largest change between consecutive output frames on a
constant input, out of 255.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### content_delta

Largest change in the constant half when the rest of the
frame changed, out of 255.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### temporal_delta

Largest change in a shared tail when the frames BEFORE
it differed, out of 255.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### determinism_delta

Largest disagreement between two applications of the
effect to the SAME input, out of 255. Nonzero means the effect is
random, and every other number in this report is then meaningless.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### can_flicker

Whether the verdict admits flicker. `None` when
undetermined — **not** `False`, because “we could not tell” and
“it cannot” are different answers and only one of them is a
guarantee.

#### note

Why, when something could not be measured.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### *class* looks.Effect(, name, params=FrozenMap(), at=None, impl=None, backend=None, metadata=FrozenMap())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One named operation the caller asks for. Pure data; no tier, no impl.

`name` is the **capability** (`"flatten"`, `"posterize"`), never an
implementation. `impl` and `backend` pin *which* answer serves
it — and neither bypasses the ceiling: a pinned implementation above the
policy is still refused, because a pin says which one you want, not that you
may have it.

`metadata` is identity-free labelling and never enters
[`look_hash()`](#looks.look_hash).

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

#### *property* refs *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[Ref](looks.spec.html.md#looks.spec.Ref), ...]*

Every deferred parameter, in no particular order.

#### resolved(probe)

A copy with every [`Ref`](#looks.Ref) replaced, or raise.

* **Return type:**
  [`Effect`](looks.spec.html.md#looks.spec.Effect)

### *class* looks.EffectRegistry(name='looks')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Effect name to implementations, and implementation key to code.

An instance rather than a module global, so a test can build its own and a
consumer can compose several. The module-level functions below delegate to
`REGISTRY`, which is the one the compiler uses by default.

### Examples

```pycon
>>> from looks.licence import terms_for
>>> reg = EffectRegistry()
>>> impl = ImplRef(effect="lut3d", impl="lut3d.ffmpeg.default",
...                backend="ffmpeg", terms=terms_for("ffmpeg")[0],
...                requires_filters=("lut3d",))
>>> _ = reg.register(impl, lambda params, **kw: {"filter": "lut3d"})
>>> reg.effects()
('lut3d',)
>>> reg.implementations("lut3d") == (impl,)
True
```

A key is taken once:

```pycon
>>> reg.register(impl, lambda params, **kw: {})
Traceback (most recent call last):
...
looks.registry.ImplConflict: 'lut3d.ffmpeg.default' is already
registered...
```

An unknown effect is an empty tuple, not an error — asking what is
available is not the same as asking for something:

```pycon
>>> reg.implementations("nonesuch")
()
```

#### compiler(key)

The code behind a key — how a stored plan becomes runnable work.

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis), [`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

#### cost(key)

The cost estimator, or `None` when none was declared.

* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis), [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]]]

#### effects()

Every effect with at least one implementation, sorted.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

#### impl(key)

The declaration behind a key.

* **Raises:**
  [**UnknownImpl**](#looks.UnknownImpl) – Naming what is available, because the usual cause is a
      plan compiled where a different set was registered.
* **Return type:**
  [`ImplRef`](looks.spec.html.md#looks.spec.ImplRef)

#### implementations(effect)

Everything registered for an effect, registration order preserved.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`ImplRef`](looks.spec.html.md#looks.spec.ImplRef), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

#### register(impl, compiler, , cost=None, tags=(), known_filters=None)

Record an implementation. Returns it, so this reads well inline.

* **Parameters:**
  * **impl** ([`ImplRef`](looks.spec.html.md#looks.spec.ImplRef)) – What the implementation declares about itself — terms, never
    a tier.
  * **compiler** ([`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis), [`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]) – `(params, *, clip, env) -> payload`. Must return plain
    data; the payload is hashed.
  * **cost** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis), [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]]]) – `(params, *, clip, env) -> float | None` in CPU-seconds.
    Absent means unknown, which is **not** zero.
  * **tags** ([`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Reserved for consumer-side search, as `xdol.Registry` has.
    Never read by selection — a tag that changed a refusal would be
    a tier a caller could assert.
  * **known_filters** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`frozenset`](https://docs.python.org/3/builtins/stdtypes.html#frozenset)]) – The filter universe to validate against. Defaults to
    the one compiled into this package. Pass a binary’s own set to
    validate against that instead.
* **Raises:**
  * [**ImplConflict**](#looks.ImplConflict) – If the key is taken.
  * [**RegistryError**](#looks.RegistryError) – If the key is not `<effect>.<backend>.<variant>`,
        or an ffmpeg implementation names a filter that does not exist.
* **Return type:**
  [`ImplRef`](looks.spec.html.md#looks.spec.ImplRef)

### *exception* looks.FfmpegBackendError

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

A step that cannot be expressed as a filter fragment.

### *class* looks.FfmpegEnv(path=None, version=None, licence=Licence.UNKNOWN, filters=frozenset({}), configuration=None, notes=())

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
  [`Licence`](looks.environment.html.md#looks.environment.Licence)

#### filters

Every filter name `ffmpeg -filters` listed. Empty when the
probe failed, which is why [`available`](#looks.FfmpegEnv.available) exists to tell “no
filters” apart from “did not look”.

* **Type:**
  [`frozenset`](https://docs.python.org/3/builtins/stdtypes.html#frozenset)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

#### configuration

The raw `configuration:` line, kept for diagnostics
only. **Never** read it to decide a licence — it is editable by the
builder, which is the whole reason [`licence`](looks.licence.html.md#module-looks.licence) comes from
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
[`filters`](#looks.FfmpegEnv.filters) empty too, and a caller must be able to tell those
apart before concluding anything.

#### fingerprint()

The comparable summary a compiled plan records.

* **Raises:**
  [**RuntimeError**](https://docs.python.org/3/builtins/exceptions.html#RuntimeError) – The probe did not run. A fingerprint of an
      environment nobody looked at would make two plans compiled
      against unknown binaries compare equal, which is the false
      direction.
* **Return type:**
  [`EnvFingerprint`](looks.environment.html.md#looks.environment.EnvFingerprint)

### Examples

```pycon
>>> FfmpegEnv().fingerprint()
Traceback (most recent call last):
...
RuntimeError: cannot fingerprint an ffmpeg that did not answer...
```

#### has_filter(name)

Whether `name` is in this build’s filter table.

Always `False` when the probe did not run — check [`available`](#looks.FfmpegEnv.available)
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

### *class* looks.FieldOfUse(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Whether the *purpose* is permitted. Orthogonal to every axis above.

No SPDX identifier carries this, so it is always a declared column and is
never parsed out of a licence id: `CC-BY-NC-SA-4.0` is a listed
identifier whose non-commercial character is not derivable from the string,
and AnimeGANv2’s terms have no identifier at all.

### *class* looks.FilterSegment(vf)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A run of ffmpeg steps with no frame operation in it: one `-vf`.

### *class* looks.FrameSegment(op, decode, encode, pix_fmt, width, height, rate, params=dict())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One ffmpeg → Python → ffmpeg segment.

Both argv are input-and-filter only. The caller appends its own encode
settings and destination to `encode`.

#### *property* frame_bytes *: [int](https://docs.python.org/3/builtins/functions.html#int)*

How many bytes one frame occupies on the pipe.

rawvideo has no header, so a consumer that guesses this reads a sheared
picture rather than an error.

### *exception* looks.GeometryError

Bases: [`ValueError`](https://docs.python.org/3/builtins/exceptions.html#ValueError)

A size or mode that cannot produce a placement.

### *class* looks.GradientMap(ramp, accent=None, contrast=1.0, lift=0.0)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A ramp, an optional accent, and the tone adjustment applied before both.

#### ramp

The main lightness-indexed ramp.

* **Type:**
  [`Ramp`](looks.lut.html.md#looks.lut.Ramp)

#### accent

An optional second ramp for a hue band the main ramp would
flatten.

* **Type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Accent`](looks.lut.html.md#looks.lut.Accent)]

#### contrast

Multiplier applied to `L*` around mid-grey before lookup.
`>1` deepens; the first real look used 1.15.

* **Type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

#### lift

`L*` offset applied after `contrast`. Negative darkens.

* **Type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### Examples

```pycon
>>> gm = GradientMap(ramp=Ramp.from_hex([(0.0, '#1B0610'), (100.0, '#FEF0DC')]))
>>> rgb_to_hex(gm(( 0.0, 0.0, 0.0)))
'#1B0610'
>>> rgb_to_hex(gm(( 1.0, 1.0, 1.0)))
'#FEF0DC'
```

#### to_dict()

A JSON-able form — the thing that is hashed for the cache key.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### *exception* looks.ImplConflict

Bases: [`RegistryError`](looks.registry.html.md#looks.registry.RegistryError)

That key is taken. Last-write-wins would change what a stored plan runs.

### *class* looks.ImplRef(, effect, impl, backend, terms, requires_filters=(), impl_version='1', timeline=True, time_varying=None, preference=0)

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
changed behaviour” bumps it, and it enters [`plan_hash()`](#looks.plan_hash)
**unconditionally**.

* **Type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

#### timeline

Whether it can be gated to an `Effect.at`. Answers a
different question from [`time_varying`](#looks.ImplRef.time_varying) and the two are close
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
[`Step.time_varying`](#looks.Step.time_varying), which also accounts for an
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
```

#### *property* tier *: [Optional](https://docs.python.org/3/library/typing.html#typing.Optional)[[Tier](looks.licence.html.md#looks.licence.Tier)]*

The rung its terms project onto, or `None` when off the ladder.

Derived on read, never stored — so it cannot drift from the terms.

### *exception* looks.Incomparable

Bases: [`MeasurementError`](#looks.MeasurementError)

Two measurements whose identity fields disagree.

Deliberately loud. The alternative — comparing them anyway — returns a
confident number produced by two different instruments, which is worse than
a refusal because nothing about it looks wrong.

### *class* looks.Keyframe(t, window)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A window, at a time in seconds from the start of the clip.

```pycon
>>> Keyframe(0.0, Window.full())
Keyframe(t=0.0, window=Window(x=0.0, y=0.0, w=1.0, h=1.0))
```

### *class* looks.Licence(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

What licence an ffmpeg build carries, as `ffmpeg -L` reports it.

Ordered from most to least permissive by `LICENCE_ORDER`. `UNKNOWN`
is deliberately *not* on that ladder: it is not a position between two
others, it is the absence of a position, and it must refuse rather than
compare.

### *exception* looks.LicenceCeilingExceeded

Bases: [`LooksLicenceError`](looks.licence.html.md#looks.licence.LooksLicenceError)

On the ladder, above the ceiling. Raise it, or pick a lower provider.

### *exception* looks.LicenceFieldRestricted

Bases: [`LooksLicenceError`](looks.licence.html.md#looks.licence.LooksLicenceError)

Non-commercial / research-only / no-derivatives. Its OWN opt-in.

### *exception* looks.LicenceForbidden

Bases: [`LooksLicenceError`](looks.licence.html.md#looks.licence.LooksLicenceError)

Off the ladder, permanently. There is no opt-in and no ceiling.

### *exception* looks.LicenceUnknown

Bases: [`LooksLicenceError`](looks.licence.html.md#looks.licence.LooksLicenceError)

Undeterminable, unprobeable, or self-contradictory. Unknown refuses.

### *class* looks.Look(\*, steps=(), name='', policy=Policy(max_tier=<Tier.COPYLEFT_TOOL: 'copyleft_tool'>, allow_field_restricted=frozenset(), order=(<Tier.PURE: 'pure'>, <Tier.PERMISSIVE: 'permissive'>, <Tier.WEAK_COPYLEFT: 'weak_copyleft'>, <Tier.COPYLEFT_TOOL: 'copyleft_tool'>, <Tier.COPYLEFT_SHIPPED: 'copyleft_shipped'>)), target=Target.EXTERNAL, metadata=FrozenMap(), version=1)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

An ordered stack of Effects plus a policy. The artifact you ship.

`a + b` concatenates the steps and takes the **stricter** of the two
policies, never the looser — a guarantee composition can silently relax is
not a guarantee. Widening is always a separate deliberate act
([`with_policy()`](#looks.Look.with_policy)).

`policy` is **not** part of [`look_hash()`](#looks.look_hash): a ceiling changes what
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

#### *property* refs *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[Ref](looks.spec.html.md#looks.spec.Ref), ...]*

Every deferred parameter across every step.

#### with_policy(policy)

A copy under a different ceiling — the deliberate widening act.

* **Return type:**
  [`Look`](looks.spec.html.md#looks.spec.Look)

### *class* looks.LookPlan(\*, steps=(), clip=None, env=None, look_name='', policy=Policy(max_tier=<Tier.COPYLEFT_TOOL: 'copyleft_tool'>, allow_field_restricted=frozenset(), order=(<Tier.PURE: 'pure'>, <Tier.PERMISSIVE: 'permissive'>, <Tier.WEAK_COPYLEFT: 'weak_copyleft'>, <Tier.COPYLEFT_TOOL: 'copyleft_tool'>, <Tier.COPYLEFT_SHIPPED: 'copyleft_shipped'>)), probe=FrozenMap(), metadata=FrozenMap(), version=1)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The compiled pipeline: what will run, against which clip and which binary.

The **env fingerprint belongs here and not on the Look**. A `Look` is
portable data; a `LookPlan` is compiled against one binary whose filter
set and licence are part of what determines the pixels — so it says which
one, and that enters [`plan_hash()`](#looks.plan_hash). Folding the environment in does not
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

The asymmetry against [`total_cpu_seconds`](#looks.LookPlan.total_cpu_seconds) is deliberate: a sum
must be total to compose, but a headline ratio a human acts on must not
fabricate. Returning `0.0` for “we did not know” is reelee#208’s
failure mode, where a `$0.00`-because-unknown read as “under the
threshold, spend freely”.

#### *property* time_varying *: [Optional](https://docs.python.org/3/library/typing.html#typing.Optional)[[bool](https://docs.python.org/3/builtins/functions.html#bool)]*

Whether any compiled step reads the clock — see [`Step.time_varying`](#looks.Step.time_varying).

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
reads the clock”, the same asymmetry [`has_unknown_costs`](#looks.LookPlan.has_unknown_costs) keeps
separate from [`total_cpu_seconds`](#looks.LookPlan.total_cpu_seconds).

#### *property* total_cpu_seconds *: [float](https://docs.python.org/3/builtins/functions.html#float)*

Sum with unknown coerced to `0.0` — a documented **lower bound**.

Total so sums compose. Read it beside [`unknown_step_count`](#looks.LookPlan.unknown_step_count), never
alone: the true cost is this *plus an unknown amount* spread over that
many steps.

#### *property* unknown_step_count *: [int](https://docs.python.org/3/builtins/functions.html#int)*

How many steps carry no cost at all.

### *exception* looks.LooksLicenceError

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

Base for every licence refusal.

### *exception* looks.LutError

Bases: [`ValueError`](https://docs.python.org/3/builtins/exceptions.html#ValueError)

A ramp or lattice that cannot produce a usable LUT.

### *class* looks.Materialised(path, key, hit)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One cube on disk, and whether this call is what put it there.

`hit` is reported rather than inferred because it is the only way a caller
can tell a cache that is working from one that is silently regenerating —
the file is identical either way, and only the clock differs.

### *exception* looks.MeasurementError

Bases: [`RuntimeError`](https://docs.python.org/3/builtins/exceptions.html#RuntimeError)

A measurement that could not be taken, or one that must not be compared.

### *exception* looks.MotionError

Bases: [`GeometryError`](looks.geometry.html.md#looks.geometry.GeometryError)

A path that cannot be compiled, or that would compile to a lie.

### *exception* looks.PipeError

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

A plan that cannot be arranged as a pipe, or not safely.

### *class* looks.PipePlan(segments, boundaries, source=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The whole arrangement, as data.

`boundaries` is the number of raw-frame crossings, which is the number
that costs — each one is a full decode and re-encode. It is reported after
folding, because counting runs before folding overstates it.

### *class* looks.Placement(source, target, scale, crop=None, offset=None, rounding='exact_floor')

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

### *exception* looks.PlanRefused

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

A stored plan that may not be run as it stands. Never a warning.

### *class* looks.Policy(, max_tier=Tier.COPYLEFT_TOOL, allow_field_restricted=frozenset({}), order=(Tier.PURE, Tier.PERMISSIVE, Tier.WEAK_COPYLEFT, Tier.COPYLEFT_TOOL, Tier.COPYLEFT_SHIPPED))

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A ceiling, plus the thing a ceiling deliberately cannot reach.

**\`\`max_tier\`\` is not the commercial-safe knob**, and saying so once here
is cheaper than the drift: every rung is commercially usable, so what
“commercial-safe only” means is `allow_field_restricted=frozenset()` —
already the default.

### Examples

```pycon
>>> Policy().max_tier
<Tier.COPYLEFT_TOOL: 'copyleft_tool'>
>>> Policy().admits(Tier.COPYLEFT_TOOL)
True
>>> Policy(max_tier=Tier.WEAK_COPYLEFT).admits(Tier.COPYLEFT_TOOL)
False
```

Off the ladder is off the ladder — no ceiling admits it:

```pycon
>>> Policy(max_tier=Tier.COPYLEFT_SHIPPED).admits(None)
False
```

#### admits(tier)

Whether the ceiling reaches `tier`. `None` is never admitted.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

#### allow_field_restricted *: [frozenset](https://docs.python.org/3/builtins/stdtypes.html#frozenset)[[FieldOfUse](looks.licence.html.md#looks.licence.FieldOfUse)]*

Which field-of-use restrictions the caller has deliberately accepted.
Empty by default, and **never** widened by `max_tier`.

#### rank(tier)

Position on *this* policy’s ladder.

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

### *class* looks.Ramp(stops)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Colours ordered by lightness — the whole specification of a gradient map.

#### stops

`(L*, rgb)` pairs, strictly increasing in `L*`, at least two.
`L*` outside a stop’s range clamps to the nearest end.

* **Type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)]], [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### Examples

```pycon
>>> r = Ramp.from_hex([(0.0, '#000000'), (100.0, '#FFFFFF')])
>>> rgb_to_hex(r.at(50.0))
'#808080'
>>> rgb_to_hex(r.at(-10.0))     # clamps
'#000000'
```

#### at(level)

The ramp colour at `L*`, linearly interpolated, clamped at the ends.

### Examples

```pycon
>>> r = Ramp.from_hex([(0.0, '#000000'), (50.0, '#FF0000'), (100.0, '#FFFFFF')])
>>> rgb_to_hex(r.at(25.0))
'#800000'
>>> rgb_to_hex(r.at(75.0))
'#FF8080'
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float), [`float`](https://docs.python.org/3/builtins/functions.html#float)]

#### *property* darkest *: [float](https://docs.python.org/3/builtins/functions.html#float)*

`L*` of the darkest stop.

### Examples

```pycon
>>> Ramp.from_hex([(8.2, '#2E0C18'), (100.0, '#FEF0DC')]).darkest
8.2
```

#### *classmethod* from_hex(stops)

Build from `(L*, '#RRGGBB')` pairs.

### Examples

```pycon
>>> Ramp.from_hex([(0.0, '#000000'), (100.0, '#FFFFFF')]).stops[1][1]
(1.0, 1.0, 1.0)
```

* **Return type:**
  [`Ramp`](looks.lut.html.md#looks.lut.Ramp)

#### *classmethod* neutral(, stops=32)

A ramp that is a true identity on greys.

\*\*A two-stop black-to-white ramp is NOT an identity, and that surprises
people.\*\* A ramp interpolates its stop colours in *sRGB* while indexing
on *L\**, and those two curves are not the same one: mid-grey sRGB 0.5
is L\* 53.39, so a naive `[(0, black), (100, white)]` ramp returns
sRGB 0.5339 for it. Measured through ffmpeg, that is an \*\*8/255 shift at
every lattice size\*\* — 17, 33 and 65 alike, which is how you know it is
systematic rather than interpolation error, and it peaks in the
midtones rather than the shadows.

This samples the inverse transfer instead, so greys survive. Use it as
the smoke test for any LUT pipeline: an identity that is not an identity
means the transfer or the lattice order is wrong.

### Examples

```pycon
>>> r = Ramp.neutral()
>>> rgb_to_hex(r.at(lightness((0.5, 0.5, 0.5))))
'#808080'
>>> rgb_to_hex(r.at(0.0)), rgb_to_hex(r.at(100.0))
('#000000', '#FFFFFF')
```

* **Return type:**
  [`Ramp`](looks.lut.html.md#looks.lut.Ramp)

#### to_dict()

A JSON-able form, for the cache key and for persisting a Look.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### *class* looks.Reach(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How far the implementation’s copyleft extends.

### *class* looks.Ref(key, default=<object object>)

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

### *class* looks.Reframe(placement, backdrop=Solid())

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

### *exception* looks.RegistryError

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

A registration that would make a later refusal point at the wrong thing.

### *exception* looks.SchemaError

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

A serialised document this build cannot read.

### *class* looks.Size(width, height)

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

### *class* looks.Solid(rgb=(0, 0, 0))

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A flat colour behind the placed frame.

### Examples

```pycon
>>> Solid().rgb
(0, 0, 0)
```

### *class* looks.Span(start=None, end=None)

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

### *exception* looks.SpanUnsupported

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

An `Effect.at` given to an implementation that cannot be gated.

### *exception* looks.SpecError

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

A Look or a plan that cannot mean what it says.

### *class* looks.Spread(choices, ratio, log_spread, dispersion, statistic, outside=())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The answer: one choice per clip, and how consistent the set now is.

`ratio` is the headline — the same number the measured rule is quoted in,
so a caller can compare it against uniform’s 2.213x directly. It is
`exp(log_spread)` and the two are reported together because the first is
what a person reads and the second is what the solver minimised.

#### outside *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), ...]* *= ()*

Clips the trim left outside the window. Empty under `full_range`.
Named rather than counted, because *which* clip could not be fixed is
the interesting half of the answer.

### *class* looks.Step(, effect, impl, tier, params=FrozenMap(), at=None, payload=FrozenMap(), cpu_seconds=None, metadata=FrozenMap())

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
one ([`Span.is_whole`](#looks.Span.is_whole), so the two never drift apart). Absent
that, the answer is exactly [`ImplRef.time_varying`](#looks.ImplRef.time_varying), unknown
included: an implementation that never declared it does not become
“does not read the clock” just because no span was given either.

### *class* looks.Target(\*values)

Bases: [`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

What a Look’s parameters resolve **against** — RULE N.

- `EXTERNAL` — a fixed target outside the material: a delivery
  contract, a reference palette, a colour conform. One clip’s probe answers
  it, and [`resolve()`](#looks.resolve) serves it.
- `SET_RELATIVE` — the target *is the set’s own distribution*. The
  answer for one clip depends on every other clip, so only
  [`resolve_across()`](#looks.resolve_across) can serve it and [`resolve()`](#looks.resolve) **raises**.

That refusal is the measured lesson as a type: normalising the OUTPUT across
sources is not a thing you can compute from one clip.

The field is `target` and **not** `intent="style"|"grade"`: a colour
conform is a *normalisation* whose target is external and fixed, and under a
style/grade wording it would have to be mislabelled.

### *class* looks.Terms(, provider, realisation, spdx, coupling, component='code', conveyance=Conveyance.UNKNOWN, field_of_use=FieldOfUse.UNKNOWN, reach=None, patents=(), conditions=(), prohibition=None, contradiction=None, verified=True, evidence=(), note='')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

What one component declares about itself. **Terms, never a tier.**

Keyed on `(provider, realisation, component)`. `realisation` is \*how
you obtain it\* — `"system"` found on PATH, `"pypi:<dist>"` conveyed by
a distribution, `"weights:<repo>"`, `"hosted:<name>"` — because that is
what makes `Conveyance.CONVEYS` expressible at all: one row per way
of getting a thing, not one row per thing. `component` is what separates
a package’s own code from the binary in its wheel, and a model’s code from
its weights: `animegan2-pytorch` is MIT code over weights with no licence
at all, and a metadata scan gets that exactly backwards.

Every default that could be a guess refuses instead: an undeclared
`conveyance` or `field_of_use` is `UNKNOWN`.

#### conditions *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), ...]*

Conditions carried as data rather than adjudicated — a revenue
threshold, a share-alike duty, a hardware floor.

#### contradiction *: [Optional](https://docs.python.org/3/library/typing.html#typing.Optional)[[str](https://docs.python.org/3/builtins/stdtypes.html#str)]*

The artifact’s own statements disagree. Refuses as UNKNOWN — looks
reports the disagreement and does not decide which statement is true.

#### *property* key *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [str](https://docs.python.org/3/builtins/stdtypes.html#str), [str](https://docs.python.org/3/builtins/stdtypes.html#str)]*

`(provider, realisation, component)`.

#### prohibition *: [Optional](https://docs.python.org/3/library/typing.html#typing.Optional)[[str](https://docs.python.org/3/builtins/stdtypes.html#str)]*

the terms grant this use to nobody
(FFmpeg’s “nonfree and unredistributable”), or to nobody here (a
territorial exclusion). Not a rung and not a field-of-use opt-in.

* **Type:**
  A recorded, unliftable prohibition

#### reach *: [Optional](https://docs.python.org/3/library/typing.html#typing.Optional)[[Reach](looks.licence.html.md#looks.licence.Reach)]*

Override the [`Reach`](#looks.Reach) derived from `spdx`. Requires a
`note`, because an unexplained override silently makes a row the
most permissive of its available readings — which is how a compound
`"Apache-2.0 AND GPL-3.0-or-later"` row once classified PERMISSIVE.

#### *property* resolved_reach *: [Reach](looks.licence.html.md#looks.licence.Reach)*

The declared reach, or the one `reach_of()` derives.

### Examples

```pycon
>>> t = Terms(provider="p", realisation="system",
...           spdx="GPL-2.0-or-later", coupling=Coupling.SUBPROCESS)
>>> t.resolved_reach
<Reach.PROGRAM: 'program'>
```

#### verified *: [bool](https://docs.python.org/3/builtins/functions.html#bool)*

`False` refuses as UNKNOWN. A row that is recorded but not established
is not a fact, and “do not cite as fact” has to be executable to hold.

### *class* looks.Tier(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

A rung on a ladder that is **policy, not fact**.

Deliberately a plain [`enum.Enum`](https://docs.python.org/3/library/enum.html#enum.Enum) with no ordering of its own, so
`<` cannot silently mean the shipped ladder when a caller supplied a
different one. Ranking goes through [`Policy.rank()`](#looks.Policy.rank).

|   rung | tier               | obligation                                                                        |
|--------|--------------------|-----------------------------------------------------------------------------------|
|      0 | `PURE`             | none — nothing external is reached                                                |
|      1 | `PERMISSIVE`       | notice retention on conveyance                                                    |
|      2 | `WEAK_COPYLEFT`    | notice + relink; dynamic linkage only                                             |
|      3 | `COPYLEFT_TOOL`    | none on your code; a prohibition on a *future*<br/>act, namely conveying the tool |
|      4 | `COPYLEFT_SHIPPED` | full source-offer duty, inherited downstream                                      |

Rungs 3 and 4 are ordered by obligation-inclusion, unambiguously. Rungs 2
and 3 are **not**: in-process LGPL and subprocess GPL impose different
duties, not more and fewer.

### *class* looks.Transition(duration_s, curve='fade')

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

### *exception* looks.TransitionError

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

A transition that cannot be honoured as asked.

### *exception* looks.UnknownFilter

Bases: [`ValueError`](https://docs.python.org/3/builtins/exceptions.html#ValueError)

A filter name that is not in any known universe.

Raised rather than ignored, because [`needs_gpl()`](#looks.needs_gpl) is an
**allowlist-by-absence**: a name it does not recognise carries no gate, so
silently returning “not GPL” for a typo, a wrong case, a filter from a newer
ffmpeg, or one an extraction never enumerated is a *computed* false
permission — at exactly the point the licence tier enters. That is the one
direction this package may never fail in.

### *exception* looks.UnknownImpl

Bases: [`RegistryError`](looks.registry.html.md#looks.registry.RegistryError)

A plan names an implementation this process does not have.

### *exception* looks.UnresolvedParameter

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

A [`Ref`](#looks.Ref) the probe did not answer, and which has no default.

Deliberately a refusal rather than a fallback. The measured lesson: one
global flattening scale made the softest of three sources softer still
(46 -> 38, against 35 -> 72 and 117 -> 114), so it became the softest thing
on screen. A silent global fallback is exactly that mistake, re-armed.

### *class* looks.Verdict(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Which region of the axis space the terms landed in.

`ON_LADDER` is **not** “admitted”. [`classify()`](#looks.classify) locates terms; it
does not apply a ceiling, and reading `ON_LADDER` as permission is the
false-permission direction. [`check()`](#looks.check) is what admits or refuses.

The other three are the regions no `max_tier` reaches, kept apart because
their remedies genuinely differ: raise the ceiling, no opt-in exists, a
separate opt-in, supply evidence.

### *class* looks.Window(x, y, w, h)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A concrete [`WindowLike`](#looks.WindowLike), for callers who do not already have one.

```pycon
>>> Window(0.25, 0.25, 0.5, 0.5)
Window(x=0.25, y=0.25, w=0.5, h=0.5)
```

The whole frame is the identity window:

```pycon
>>> Window.full()
Window(x=0.0, y=0.0, w=1.0, h=1.0)
```

### *class* looks.WindowLike(\*args, \*\*kwargs)

Bases: [`Protocol`](https://docs.python.org/3/library/typing.html#typing.Protocol)

Burns’ convention: normalised, top-left origin, window fractions.

Structural on purpose — `burns.Rect` satisfies it without `looks`
importing `burns`, and so does anything else a caller already has.

### looks.assert_flicker_free(chain, \*\*kwargs)

Raise unless `chain` provably cannot flicker.

\*\*What a pass means, precisely: three probes could not make this effect
depend on anything they varied.\*\* It is not a proof of frame independence —
`tblend` and `atadenoise` pass and are temporal. For an effect whose class
matters, pair this with the structural argument (a stateless per-pixel
lookup cannot depend on anything else) or with a declared class this
function is used to *falsify*.

An `UNDETERMINED` verdict **raises**: “we could not tell” must not be
reported as “it cannot”, which is the same unknown-is-a-refusal rule the
licence tier follows, applied to the other guarantee this package makes.

* **Raises:**
  [**AssertionError**](https://docs.python.org/3/builtins/exceptions.html#AssertionError) – The chain can flicker, or could not be shown not to.
* **Return type:**
  [`DependencyReport`](looks.frame_dependency.html.md#looks.frame_dependency.DependencyReport)

### looks.assess(terms, , order=(Tier.PURE, Tier.PERMISSIVE, Tier.WEAK_COPYLEFT, Tier.COPYLEFT_TOOL, Tier.COPYLEFT_SHIPPED), today=None)

Assess a provider made of several components: **the worst one wins.**

Deliberately *not* a per-axis join. Join OpenCV’s Apache-2.0 in-process C++
with the GPL ffmpeg conveyed in the same wheel and you get “we link a GPL
program in-process” — a chimera true of neither component, which then
classifies FORBIDDEN. Each component keeps its own row, the caller sees
which half is the problem, and [`check()`](#looks.check) applies the ceiling to \*\*every
part\*\*, so `order` only decides which component gets named first.

### Examples

```pycon
>>> code = Terms(provider="moviepy", realisation="pypi:moviepy",
...              spdx="MIT", coupling=Coupling.IN_PROCESS,
...              conveyance=Conveyance.CONVEYS,
...              field_of_use=FieldOfUse.UNRESTRICTED)
>>> shipped = Terms(provider="moviepy", realisation="pypi:moviepy",
...                 component="transitive", spdx="GPL-2.0-or-later",
...                 coupling=Coupling.SUBPROCESS,
...                 conveyance=Conveyance.CONVEYS,
...                 field_of_use=FieldOfUse.UNRESTRICTED)
>>> classify(code).tier
<Tier.PERMISSIVE: 'permissive'>
>>> assess([code, shipped]).tier
<Tier.COPYLEFT_SHIPPED: 'copyleft_shipped'>
>>> len(assess([code, shipped]).parts)
2
```

* **Return type:**
  [`Assessment`](looks.licence.html.md#looks.licence.Assessment)

### looks.assess_ffmpeg_chain(filters, , env, realisation='system', today=None)

The licence position of a filter chain on one probed binary.

Joins the two things [`looks.environment`](looks.environment.html.md#module-looks.environment) already answers — what the
binary’s `-L` says, and which filters FFmpeg gates behind
`--enable-gpl` — without restating either.

Three rules, in the order they bite:

1. **A nonfree build is refused first**, before any ceiling comparison.
2. \*\*A GPL-gated filter does not raise the tier; the binary already has
   it.\*\* Every filter in a GPL build is reached through a GPL program, so
   the chain’s position is the *binary’s* rung. What the gated filters
   change is the *reason*, which the refusal message needs: an `eq` look
   does not merely cost more obligations, it does not exist on an LGPL
   build at all.
3. **A disagreement between the two authorities refuses.** A binary whose
   `-L` says LGPL while it carries filters FFmpeg gates behind
   `--enable-gpl` is contradicting itself, exactly as `av` does, and
   `looks` reports the disagreement rather than picking a side.

Availability is reported, never refused here: a filter absent from the
declared environment is a compile-time refusal (it is the *stronger* check,
catching `--disable-filter=eq` on a GPL build, which no tier table can),
and that refusal belongs to the compiler. It arrives as an advisory.

* **Raises:**
  [**UnknownFilter**](looks.environment.html.md#looks.environment.UnknownFilter) – A name that is not an ffmpeg filter.
      Deliberately not swallowed: this function reports a name carrying
      no gate as GPL-free, so an unrecognised one would be a *computed*
      false permission at the licence tier’s entry point.
* **Return type:**
  [`Assessment`](looks.licence.html.md#looks.licence.Assessment)

### Examples

```pycon
>>> gpl = FfmpegEnv(path='/opt/homebrew/bin/ffmpeg',
...                 licence=Licence.GPL3,
...                 filters=frozenset({'lut3d', 'lutrgb', 'eq'}))
>>> a = assess_ffmpeg_chain(['lut3d', 'lutrgb'], env=gpl)
>>> a.tier
<Tier.COPYLEFT_TOOL: 'copyleft_tool'>
```

The Que Calor chain is LGPL-clean, so the same chain on an LGPL build
is two rungs lower — and the grade filter everyone reaches for is not:

```pycon
>>> lgpl = FfmpegEnv(path='/usr/local/bin/ffmpeg-lgpl',
...                  licence=Licence.LGPL21,
...                  filters=frozenset({'lut3d', 'lutrgb'}))
>>> assess_ffmpeg_chain(['lut3d', 'lutrgb'], env=lgpl).tier
<Tier.WEAK_COPYLEFT: 'weak_copyleft'>
>>> assess_ffmpeg_chain(['eq'], env=gpl).reasons[0]
"it reaches filters FFmpeg gates behind --enable-gpl: ('eq',)"
```

### looks.audit(plan, , policy=None, registry=None)

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
  * [**PlanRefused**](#looks.PlanRefused) – If a step names an implementation this process lacks, or
        one whose `impl_version` has moved, or one whose stored tier
        disagrees with its terms.
  * [**LooksLicenceError**](looks.licence.html.md#looks.licence.LooksLicenceError) – If a step exceeds the ceiling.
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### looks.blended_frames(transition, fps, , offset=None)

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
under-reported — the safe direction for [`is_hard_cut()`](#looks.is_hard_cut), but it
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

### looks.cache_dir(into=None)

Where cubes are kept, resolved in one place.

`into` wins, then `$LOOKS_CACHE_DIR`, then the platform cache directory.
The directory is created if absent — a cache that refuses to exist is not a
cache.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### looks.check(assessment, policy, subject, , alternatives=())

Raise unless `policy` admits `assessment`. Returns `None` on pass.

Every component is checked, loudest first, so a composite can never admit
something one of its parts would not — and so the message names the
component that is actually the problem.

A refusal message names, in order: the subject, the tier it needs, the
ceiling in force, *why* (the resolved provider and the dated observations
that decided it), how to opt in, and any lower-tier alternative. A refusal
that only says no is the one people remove.

* **Parameters:**
  * **assessment** ([`Assessment`](looks.licence.html.md#looks.licence.Assessment)) – From [`classify()`](#looks.classify) or [`assess()`](#looks.assess).
  * **policy** ([`Policy`](looks.licence.html.md#looks.licence.Policy)) – The ceiling in force, plus any field-of-use opt-in.
  * **subject** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – What is being refused — an effect name, an implementation id.
  * **alternatives** ([`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Lower-tier implementations of the same capability, named
    in the message.
* **Raises:**
  * [**LicenceForbidden**](#looks.LicenceForbidden) – Off the ladder permanently; no opt-in exists.
  * [**LicenceUnknown**](#looks.LicenceUnknown) – Undeterminable, unverified, or self-contradictory.
  * [**LicenceFieldRestricted**](#looks.LicenceFieldRestricted) – Restricted purpose, and no opt-in was given.
  * [**LicenceCeilingExceeded**](#looks.LicenceCeilingExceeded) – On the ladder, above the ceiling.
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### Examples

```pycon
>>> ffmpeg = classify(Terms(
...     provider="ffmpeg", realisation="system", component="binary",
...     spdx="GPL-3.0-or-later", coupling=Coupling.SUBPROCESS,
...     conveyance=Conveyance.FINDS,
...     field_of_use=FieldOfUse.UNRESTRICTED))
>>> check(ffmpeg, DFLT_POLICY, "effect 'gamma'") is None
True
>>> check(ffmpeg, Policy(max_tier=Tier.WEAK_COPYLEFT), "effect 'gamma'")
Traceback (most recent call last):
    ...
looks.licence.LicenceCeilingExceeded: ...
```

The refusal says what it is protecting against, and what to do:

```pycon
>>> try:
...     check(ffmpeg, Policy(max_tier=Tier.WEAK_COPYLEFT), "'gamma'",
...           alternatives=["gamma.ffmpeg.lutyuv"])
... except LicenceCeilingExceeded as e:
...     print(str(e).splitlines()[0])
'gamma' needs tier COPYLEFT_TOOL; the ceiling in force is WEAK_COPYLEFT.
```

### looks.check_visible(transition, fps, , offset=None)

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

### looks.classify(terms, , today=None)

Locate `terms` in the axis space. Applies **no** ceiling.

The branch order is the design, and two things about it are load-bearing.

**A field-restricted assessment still carries its ladder rung.** Dropping
it is how the first version of this design let `Policy(max_tier=PURE,
allow_field_restricted={NON_COMMERCIAL})` admit a subprocess GPL-3
conveying provider: the opt-in was honoured, there was no tier left, and
the ceiling test never ran.

\*\*Record-level unknowns come before the region checks; axis-level unknowns
come after the field check.\*\* If the record cannot be trusted at all — it
is unverified, or the artifact contradicts itself — nothing may be
concluded from its axes. But a row whose reach is unreadable while its
field of use is plainly non-commercial is more usefully refused as
field-restricted, and nothing leaks: opting into that field leaves
`tier is None`, and the ceiling test refuses it as unknown.

### Examples

```pycon
>>> ffmpeg = Terms(provider="ffmpeg", realisation="system",
...                component="binary", spdx="GPL-3.0-or-later",
...                coupling=Coupling.SUBPROCESS,
...                conveyance=Conveyance.FINDS,
...                field_of_use=FieldOfUse.UNRESTRICTED)
>>> a = classify(ffmpeg)
>>> a.verdict, a.tier
(<Verdict.ON_LADDER: 'on_ladder'>, <Tier.COPYLEFT_TOOL: 'copyleft_tool'>)
```

A field-restricted row keeps its rung, which is what the ceiling test
needs after an opt-in is honoured:

```pycon
>>> nc = Terms(provider="m", realisation="weights:m", component="weights",
...            spdx="GPL-3.0-or-later", coupling=Coupling.SUBPROCESS,
...            conveyance=Conveyance.CONVEYS,
...            field_of_use=FieldOfUse.NON_COMMERCIAL)
>>> classify(nc).verdict, classify(nc).tier
(<Verdict.FIELD_RESTRICTED: 'field_restricted'>, <Tier.COPYLEFT_SHIPPED: 'copyleft_shipped'>)
```

Unknown is a refusal, and it is a *different* refusal:

```pycon
>>> classify(Terms(provider="x", realisation="pypi:x",
...                spdx="LicenseRef-nobody-wrote-one",
...                coupling=Coupling.IN_PROCESS,
...                conveyance=Conveyance.CONVEYS)).verdict
<Verdict.UNKNOWN: 'unknown'>
```

* **Return type:**
  [`Assessment`](looks.licence.html.md#looks.licence.Assessment)

### looks.classify_dependency(chain, , ffprobe='ffprobe', timeout=120.0)

Measure what `chain` depends on.

* **Parameters:**
  * **chain** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – An ffmpeg filter chain, as it would appear in `-vf`.
  * **ffprobe** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Binary name or path.
  * **timeout** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – Seconds per probe.
* **Return type:**
  [`DependencyReport`](looks.frame_dependency.html.md#looks.frame_dependency.DependencyReport)

### Examples

```pycon
>>> classify('lut3d=look.cube').dependency
<Dependency.INDEPENDENT: 'independent'>
>>> classify('normalize').can_flicker
True
```

### looks.color_range(source, , ffprobe='ffprobe', timeout=30.0)

What range `source` **declares**, with `untagged` as a real answer.

Not “probably limited”. ffmpeg writes untagged files by default, so the
untagged case is the normal one, and treating it as limited is an
assumption the caller should get to see rather than inherit.

* **Return type:**
  [`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'limited'`, `'full'`, `'untagged'`]

### looks.compare(a, b)

Raise [`Incomparable`](#looks.Incomparable) unless `a` and `b` can be compared.

Call this before any arithmetic that puts two measurements in the same
expression. It is cheap, and the failure it prevents is silent.

### Examples

```pycon
>>> base = dict(instrument='ffmpeg-8.1/siti', luma_space='coded_y',
...             sample_spec='uniform:5', n_frames=5)
>>> a = ClipStats(source_id='c01', stage='post_effect', **base)
>>> b = ClipStats(source_id='c02', stage='post_effect', **base)
>>> compare(a, b)
```

Different stages are the mistake the whole module exists to prevent:

```pycon
>>> c = ClipStats(source_id='c02', stage='source', **base)
>>> compare(a, c)
Traceback (most recent call last):
...
looks.measure.Incomparable: 'c01' and 'c02' were measured differently
and cannot be compared: stage 'post_effect' vs 'source'...
```

So is a different luma space, and this one is the 29x trap:

```pycon
>>> d = ClipStats(source_id='c02', stage='post_effect',
...               instrument='ffmpeg-8.1/siti', luma_space='bgr2gray',
...               sample_spec='uniform:5', n_frames=5)
>>> compare(a, d)
Traceback (most recent call last):
...
looks.measure.Incomparable: ...luma_space 'coded_y' vs 'bgr2gray'...
```

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

### looks.compile_look(look, , clip=None, env=None, policy=None, probe={}, registry=None)

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
  * [**CompileError**](#looks.CompileError) – If an effect has no admissible implementation. The
        message says which constraint emptied the pool, because “no
        implementation available” alone is the least useful refusal in the
        package.
  * [**LooksLicenceError**](looks.licence.html.md#looks.licence.LooksLicenceError) – If the selected implementation exceeds
        the ceiling. Selection already filters by policy, so this fires
        only when nothing admissible existed.

### looks.compile_motion(keyframes, , output=None, fps=None, aspect_tolerance=1e-06)

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
inside it. See [`reframe()`](#looks.reframe).

```pycon
>>> compile_motion(
...     [Keyframe(0.0, Window(0.0, 0.2, 1.0, 0.5)),
...      Keyframe(2.0, Window(0.1, 0.3, 0.8, 0.4))],
...     output=Size(1920, 1080), fps=25,
... ).startswith("crop=")
True
```

* **Raises:**
  [**MotionError**](#looks.MotionError) – If a zoom is asked for without `output` and `fps`.
      They are not defaultable: `zoompan`’s own `fps` default retimes
      the clip, and there is no honest guess for a delivery size.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.crop_fragment(keyframes)

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
  [**MotionError**](#looks.MotionError) – If the window’s size varies. `crop`’s `w`/`h` do not
      accept `t` — the filter refuses to configure — so this is not a
      missing feature that could be added later.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.cube_file(spec, , size=33, title='looks_gradient_map', into=None)

Ensure the cube for `spec` exists on disk, and say where.

Idempotent and safe to call concurrently. The second caller finds the file
the first one wrote; a caller racing another mid-write finds either the
complete previous file or the complete new one, never a partial.

* **Parameters:**
  * **size** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – The lattice size. Part of the address — a 17-cube and a 33-cube of
    one ramp are different files.
  * **title** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Written into the file’s first line, and therefore into the
    address. See [`looks.lut.cube_key()`](looks.lut.html.md#looks.lut.cube_key).
  * **into** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path), [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – The cache directory. Defaults to [`cache_dir()`](#looks.cache_dir).
* **Return type:**
  [`Materialised`](looks.cache.html.md#looks.cache.Materialised)

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

### looks.cube_key(spec, , size=33, title='looks_gradient_map')

A content hash of everything that determines the file’s bytes.

A 33-cube is ~950 KB, so a `.cube` is a \*\*build artifact generated into a
cache\*\*, never committed and never carried inside a Look. The ramp is the
spec; this is its address. Two Looks with the same ramp share one file, and
a changed ramp cannot reuse a stale one.

### Examples

```pycon
>>> r = Ramp.from_hex([(0.0, '#000000'), (100.0, '#FFFFFF')])
>>> a, b = cube_key(r), cube_key(r)
>>> a == b and len(a) == 64
True
>>> cube_key(r, size=17) == cube_key(r, size=33)   # size is identity
False
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.cube_text(spec, , size=33, title='looks_gradient_map')

Render an Iridas `.cube` for `spec`, as text.

The lattice order is the format’s own: **red varies fastest**, then green,
then blue. Getting that backwards produces a file that loads without
complaint and swaps the red and blue axes of every colour, which is the
single easiest way to be wrong here.

* **Parameters:**
  * **spec** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`Ramp`](looks.lut.html.md#looks.lut.Ramp), [`GradientMap`](looks.lut.html.md#looks.lut.GradientMap)]) – A [`Ramp`](#looks.Ramp) (used with default tone) or a [`GradientMap`](#looks.GradientMap).
  * **size** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – Lattice edge length. 2 is legal and useful for tests.
  * **title** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Written into the file’s `TITLE` line.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### Examples

```pycon
>>> ramp = Ramp.from_hex([(0.0, '#000000'), (100.0, '#FFFFFF')])
>>> text = cube_text(ramp, size=2)
>>> print(text.splitlines()[0])
TITLE "looks_gradient_map"
>>> print(text.splitlines()[1])
LUT_3D_SIZE 2
```

Red fastest: entry 1 is (r=1, g=0, b=0), which for a neutral ramp is a
dark grey rather than a bright one, because red carries only 21% of
luminance.

```pycon
>>> first, second = text.splitlines()[5], text.splitlines()[6]
>>> [round(float(x), 3) for x in first.split()]
[0.0, 0.0, 0.0]
>>> round(float(second.split()[0]), 3)
0.532
```

### looks.describe(plan)

A plan as a few lines of text — for a CLI, a log, or a review.

Deliberately not a round-trippable format. Serialisation is
[`looks.spec.plan_to_dict()`](looks.spec.html.md#looks.spec.plan_to_dict)’s job, and a second one would be a second
thing to keep in sync.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.dispersion(stats, , key='sharpness')

The max/min ratio of `key` across `stats` — the quantity to minimise.

A **ratio**, not a variance, for two reasons. Every figure the source
material reports is one (“2.98x -> 1.59x”, “205% retained”, “0.89-1.12x”),
and the statistic is positive and multiplicative, so a variance in raw units
would let one bright clip dominate.

Every pair is checked with [`compare()`](#looks.compare) first.

### Examples

```pycon
>>> base = dict(stage='post_effect', instrument='i', luma_space='coded_y',
...             sample_spec='s', n_frames=5)
>>> before = [ClipStats(source_id=n, sharpness=v, **base)
...           for n, v in [('c01', 72.2), ('c02', 114.3), ('c03', 38.4)]]
>>> round(dispersion(before), 2)          # the shipped V2b spread
2.98
>>> after = [ClipStats(source_id=n, sharpness=v, **base)
...          for n, v in [('c01', 72.2), ('c02', 114.3), ('c03', 71.8)]]
>>> round(dispersion(after), 2)           # V2c, after the per-clip fix
1.59
```

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### looks.effects()

Every effect `REGISTRY` can serve.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.escape_filter_value(value)

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

### looks.ffmpeg_chain(placement, , backdrop=None)

The resolved `scale,crop,pad` chain for one placement.

**Resolved, not deferred.** ffmpeg can express fit and fill without knowing
the source size, via `scale=W:H:force_original_aspect_ratio=decrease`, and
that form is nearly identical — but *nearly* is the problem: it rounds where
this floors, so 1920x1080 into 1080x1920 differs by one row and the seam
goes black-to-white. More fundamentally, a placement that does not know its
source size cannot be inspected or diffed, which is the premise of the whole
package. Resolve against the clip, then emit.

Only a solid backdrop is emitted here; a [`Blurred`](#looks.Blurred) backdrop needs a
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

### looks.ffmpeg_terms(env, , realisation='system', today=None)

One probed ffmpeg binary, as [`Terms`](#looks.Terms).

**The environment is an argument.** This takes an [`FfmpegEnv`](#looks.FfmpegEnv) a
caller probed and never probes for itself, because there is not one ffmpeg
on a machine: measured on the machine this package was written on, `PATH`
is 8.1 / GPL-3 / 481 filters while `imageio-ffmpeg`’s bundled binary is
7.1 / GPL-2 / 484, and the filter sets are non-nested. A component that
probes on its own behalf silently binds to whichever binary was first on
`PATH`.

* **Parameters:**
  * **env** ([`FfmpegEnv`](looks.environment.html.md#looks.environment.FfmpegEnv)) – From [`looks.environment.probe()`](looks.environment.html.md#looks.environment.probe).
  * **realisation** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – How this binary was obtained — `"system"` for found on
    `PATH`, `"pypi:<dist>"` for one a distribution ships. It is
    what decides [`Conveyance`](#looks.Conveyance), and therefore rung 3 versus 4.
  * **today** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`date`](https://docs.python.org/3/library/datetime.html#datetime.date)]) – Stamped on the evidence; for tests.
* **Return type:**
  [`Terms`](looks.licence.html.md#looks.licence.Terms)

### Examples

```pycon
>>> gpl = FfmpegEnv(path='/opt/homebrew/bin/ffmpeg',
...                 version='ffmpeg version 8.1',
...                 licence=Licence.GPL3,
...                 filters=frozenset({'lut3d', 'eq'}))
>>> classify(ffmpeg_terms(gpl)).tier
<Tier.COPYLEFT_TOOL: 'copyleft_tool'>
```

The same source, built without `--enable-gpl`, is two rungs lower —
which is the whole reason a tier cannot be a constant:

```pycon
>>> lgpl = FfmpegEnv(path='/usr/local/bin/ffmpeg-lgpl',
...                  licence=Licence.LGPL21,
...                  filters=frozenset({'lut3d'}))
>>> classify(ffmpeg_terms(lgpl)).tier
<Tier.WEAK_COPYLEFT: 'weak_copyleft'>
```

A binary nobody probed is unknown, and unknown refuses:

```pycon
>>> classify(ffmpeg_terms(FfmpegEnv())).verdict
<Verdict.UNKNOWN: 'unknown'>
```

### looks.filter_string(name, options=None)

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

### looks.gpl_only_filters()

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

### looks.gradient_map(ramp, , accent=None, contrast=1.0, lift=0.0)

Build a [`GradientMap`](#looks.GradientMap), warning about a ramp that reaches black.

The warning is the encoded form of a measured mistake: a ramp whose dark end
sat at L\* 3.6 crushed 16.2% of pixels into the bottom bin, where the
reference it was matching had 0.3%. The reference’s own floor was an
oxblood at L\* 8.22 — it had **no true black at all**.

### Examples

```pycon
>>> import warnings
>>> ok = gradient_map(Ramp.from_hex([(8.2, '#2E0C18'), (100.0, '#FEF0DC')]))
>>> ok.ramp.darkest
8.2
```

```pycon
>>> with warnings.catch_warnings(record=True) as w:
...     warnings.simplefilter('always')
...     _ = gradient_map(Ramp.from_hex([(0.0, '#000000'), (100.0, '#FFFFFF')]))
...     print(str(w[0].message)[:43])
ramp reaches L* 0.0, below the L* 5.0 floor
```

* **Return type:**
  [`GradientMap`](looks.lut.html.md#looks.lut.GradientMap)

### looks.is_hard_cut(transition, fps, , offset=None)

Will this transition produce no blended frame at all?

Without `offset` this is “might it blend nothing, at some offset” — the
conservative reading, since [`blended_frames()`](#looks.blended_frames) returns the minimum.
With one it is the exact answer for that placement.

```pycon
>>> is_hard_cut(Transition(0.30), 30)
False
>>> is_hard_cut(Transition(0.10), 10)
True
```

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### looks.is_source_shaped(keyframes)

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

### looks.known_filters()

Every filter name FFmpeg n8.1 declares — the universe [`needs_gpl()`](#looks.needs_gpl) checks against.

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

### looks.look_from_dict(d)

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
  [`Look`](looks.spec.html.md#looks.spec.Look)

### looks.look_hash(look)

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

### looks.look_to_dict(look)

A JSON-able form of a Look, carrying its schema tag.

### Examples

```pycon
>>> d = look_to_dict(Look(name="x", steps=(Effect(name="lut3d"),)))
>>> d["schema"], d["name"]
('looks.look/v1', 'x')
```

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### looks.materialize(plan, , into=None)

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

A plan is built here by hand rather than by [`looks.compile_look()`](#looks.compile_look),
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

### looks.measure(source, , source_id='', vf='', frames=5, fps=1.0, ffmpeg_version='unknown', ffprobe='ffprobe', timeout=120.0)

Measure one clip, at the source or through a Look’s compiled chain.

Supplying `vf` makes this a `post_effect` measurement, which is the one
that governs a resolver’s answer.

`ffmpeg_version` enters [`ClipStats.instrument`](#looks.ClipStats.instrument), so pass the version
from a [`looks.environment.FfmpegEnv`](looks.environment.html.md#looks.environment.FfmpegEnv) rather than letting it default —
the filters’ outputs are version-dependent, and `unknown` is honest but
makes every measurement incomparable with a properly-labelled one, which is
the intended pressure.

* **Raises:**
  [**MeasurementError**](#looks.MeasurementError) – The probe could not run.
* **Return type:**
  [`ClipStats`](#looks.ClipStats)

### looks.needs_gpl(filters, , known=None)

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
    [`FfmpegEnv.filters`](#looks.FfmpegEnv.filters) to also catch a name this build does not
    have; the default is [`known_filters()`](#looks.known_filters), every filter FFmpeg
    n8.1 declares.
* **Raises:**
  [**UnknownFilter**](#looks.UnknownFilter) – A name is not in `known`.
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

### looks.output_key(plan, source_digest)

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

### looks.payloads(plan, backend=None)

Every step’s payload, optionally for one backend.

The reading surface for a stored plan: an `ffmpeg` payload is fully
inspectable, so this is how a caller sees the exact filtergraph a plan
stands for without running anything.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.pending(plan)

The cube addresses this plan needs and has not been given.

Empty means the plan is ready to run. This is the question a caller should
ask before handing a plan to a backend, and it is what
[`looks.ffmpeg.vf()`](looks.ffmpeg.html.md#looks.ffmpeg.vf) answers with a refusal rather than a guess.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.pipe_plan(plan, , source, clip=None, pix_fmt='bgr24')

Arrange a compiled plan as processes — emitted as data, never started.

* **Parameters:**
  * **source** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – What the first decoder reads. Passed through verbatim; `looks`
    does not open it.
  * **clip** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`ClipSpec`](looks.spec.html.md#looks.spec.ClipSpec)]) – The clip the plan was compiled against. Defaults to the plan’s own.
* **Raises:**
  [**PipeError**](#looks.PipeError) – If the plan needs a raw-frame boundary and cannot be arranged
      safely across it — an undeclared time origin under a gated step, or
      a gate baked into a filter string.
* **Return type:**
  [`PipePlan`](looks.pipe.html.md#looks.pipe.PipePlan)

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

### looks.placement(source, target, , mode='fit', rounding='exact_floor')

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
  [`Placement`](looks.geometry.html.md#looks.geometry.Placement)

### looks.plan_from_dict(d, , impls)

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
  [**SchemaError**](#looks.SchemaError) – An unrecognised schema tag, or a step naming an
      implementation `impls` does not carry.
* **Return type:**
  [`LookPlan`](looks.spec.html.md#looks.spec.LookPlan)

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

### looks.plan_hash(plan)

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

### looks.plan_to_dict(plan)

A JSON-able form of a plan, carrying its schema tag.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### looks.probe(ffmpeg='ffmpeg', , timeout=20.0)

Interrogate one ffmpeg binary. Three subprocess calls, no input, no output.

Returns a [`FfmpegEnv`](#looks.FfmpegEnv) in every case, including when `ffmpeg` is not
installed — the absence of a binary is a fact about the machine, and a
caller diagnosing it needs a value rather than an exception.

* **Parameters:**
  * **ffmpeg** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – Binary name (looked up on `PATH`) or an explicit path.
  * **timeout** ([`float`](https://docs.python.org/3/builtins/functions.html#float)) – Seconds allowed per probe call.
* **Return type:**
  [`FfmpegEnv`](looks.environment.html.md#looks.environment.FfmpegEnv)

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

### looks.probes_for(spread, parameter)

A [`Spread`](#looks.Spread) as the probes [`looks.resolve_across()`](#looks.resolve_across) takes.

The join between the two halves of RULE N: this module answers the
set-relative question, and `resolve_across` applies the answer, turning
each `SET_RELATIVE` Look into an `EXTERNAL` one that will not be asked
again against a different set.

* **Parameters:**
  **parameter** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – The [`Ref`](looks.spec.html.md#looks.spec.Ref) key the value fills in.
* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### Examples

```pycon
>>> spread = Spread(choices=(Choice('c01', 0.75, 40.0),
...                          Choice('c02', 0.5, 42.0)),
...                 ratio=1.05, log_spread=0.049,
...                 dispersion='full_range', statistic='sharpness')
>>> probes_for(spread, 'scale')
({'scale': 0.75}, {'scale': 0.5})
```

### looks.reframe(source, target, , mode='fit', backdrop=None, rounding='exact_floor')

[`placement()`](#looks.placement) plus a backdrop.

* **Return type:**
  [`Reframe`](looks.geometry.html.md#looks.geometry.Reframe)

### looks.reframe_motion(keyframes, , aspect_tolerance=1e-06)

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
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Window`](looks.motion.html.md#looks.motion.Window)], [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Keyframe`](looks.motion.html.md#looks.motion.Keyframe), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]]
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
  [**MotionError**](#looks.MotionError) – If the windows are not all the same shape (an anisotropic
      zoom, which `zoompan` cannot express at all), or if the source
      cannot supply a frame of the needed aspect containing the whole path.
* **Return type:**
  [*tuple*](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[*Window*](looks.motion.html.md#looks.motion.Window) | *None*, [*tuple*](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[*Keyframe*](looks.motion.html.md#looks.motion.Keyframe), …]]

### looks.register_defaults(registry=None)

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

### looks.register_effect(impl, compiler, \*\*kwargs)

Register into `REGISTRY`. See [`EffectRegistry.register()`](#looks.EffectRegistry.register).

* **Return type:**
  [`ImplRef`](looks.spec.html.md#looks.spec.ImplRef)

### looks.resolve(look, probe={})

Replace every [`Ref`](#looks.Ref) from one clip’s `probe`.

The **identity** on a Look holding no Refs, so a caller who already has
numbers never meets this function.

* **Raises:**
  * [**SpecError**](#looks.SpecError) – The Look is `SET_RELATIVE` — RULE N. Its target is the
        set’s own distribution, which one clip cannot supply.
  * [**UnresolvedParameter**](#looks.UnresolvedParameter) – A Ref with no default that `probe` does not
        answer.
* **Return type:**
  [`Look`](looks.spec.html.md#looks.spec.Look)

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

### looks.resolve_across(look, probes)

One resolved Look per probe — N in, N out.

The resolver for a target that is the set’s own distribution. This function
does **not** compute the cross-clip answer: it applies per-clip probes a
caller has already solved for, because choosing them requires running the
effect, and running things is not this package’s job. See
[`looks.measure`](#looks.measure) for the measurement half.

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
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Look`](looks.spec.html.md#looks.spec.Look), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.runs(plan)

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

### looks.scaled_size(source, target, , mode='fit', rounding='exact_floor')

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
  [`Size`](looks.geometry.html.md#looks.geometry.Size)

### looks.select_impl(effect, candidates, \*, policy=Policy(max_tier=<Tier.COPYLEFT_TOOL: 'copyleft_tool'>, allow_field_restricted=frozenset(), order=(<Tier.PURE: 'pure'>, <Tier.PERMISSIVE: 'permissive'>, <Tier.WEAK_COPYLEFT: 'weak_copyleft'>, <Tier.COPYLEFT_TOOL: 'copyleft_tool'>, <Tier.COPYLEFT_SHIPPED: 'copyleft_shipped'>)), available_filters=None)

Choose an implementation for `effect`, or raise saying why not.

In order: honour an explicit `impl` or `backend` pin, drop anything the
environment cannot run, drop anything the policy refuses, drop anything that
cannot be gated when the effect has a span, then take the lowest tier and
break ties on [`ImplRef.preference`](#looks.ImplRef.preference).

**A pin narrows, it never permits.** A pinned implementation the policy
refuses is still refused — otherwise the pin is a way to assert a tier,
which is the thing [`Effect`](#looks.Effect) deliberately cannot do.

* **Raises:**
  * [**SpecError**](#looks.SpecError) – Nothing survived, with the reason.
  * [**SpanUnsupported**](#looks.SpanUnsupported) – Every survivor refuses a span the effect carries.
* **Return type:**
  [`ImplRef`](looks.spec.html.md#looks.spec.ImplRef)

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

### looks.snap_even(size)

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
  [`Size`](looks.geometry.html.md#looks.geometry.Size)

### looks.social_size(name)

Resolve a `SOCIAL_SIZES` preset name.

A convenience over [`Size`](#looks.Size), never a parallel vocabulary — nothing else
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
  [`Size`](looks.geometry.html.md#looks.geometry.Size)

### looks.solve_across(candidates, , statistic='sharpness', objective='min_spread', dispersion='full_range', drop=0)

One parameter value per clip, so the set’s measurements sit close together.

* **Parameters:**
  * **candidates** ([`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`Candidate`](looks.across.html.md#looks.across.Candidate)]]) – `{source_id: [Candidate, ...]}` — the grid, already
    measured. This module does not measure; see [`looks.measure`](#looks.measure).
  * **statistic** ([`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'sharpness'`, `'blur'`]) – Which measurement to make consistent.
  * **objective** ([`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'min_spread'`]) – `"min_spread"`, and only that. See `Objective`.
  * **dispersion** ([`Literal`](https://docs.python.org/3/library/typing.html#typing.Literal)[`'full_range'`, `'trimmed_range'`]) – `"full_range"` (max/min over every clip) or
    `"trimmed_range"` (allow `drop` clips outside the window).
  * **drop** ([`int`](https://docs.python.org/3/builtins/functions.html#int)) – How many clips may sit outside. Only with `trimmed_range`.
* **Raises:**
  [**AcrossError**](#looks.AcrossError) – If the inputs cannot yield an answer — no clips, a clip
      with an empty grid, measurements that are not comparable with each
      other, a missing or non-positive statistic, or a `drop` that would
      leave nothing to be consistent about.
* **Return type:**
  [`Spread`](looks.across.html.md#looks.across.Spread)

### Examples

Three clips, each with two candidates. The solver picks the combination
whose measurements sit closest together, not the sharpest one each:

```pycon
>>> def stats(source_id, sharpness):
...     return ClipStats(source_id=source_id, stage='post_effect',
...                      instrument='x', luma_space='coded_y',
...                      sample_spec='uniform:5', n_frames=5,
...                      sharpness=sharpness)
>>> got = solve_across({
...     'c01': [Candidate(0.5, stats('c01', 100.0)),
...             Candidate(0.75, stats('c01', 40.0))],
...     'c02': [Candidate(0.5, stats('c02', 42.0)),
...             Candidate(0.75, stats('c02', 20.0))],
...     'c03': [Candidate(0.5, stats('c03', 38.0)),
...             Candidate(0.75, stats('c03', 12.0))],
... })
>>> [(c.source_id, c.value) for c in got.choices]
[('c01', 0.75), ('c02', 0.5), ('c03', 0.5)]
>>> round(got.ratio, 3)
1.105
```

Choosing the sharpest everywhere would have been far worse:

```pycon
>>> round(100.0 / 38.0, 3)
2.632
```

### looks.sweep(into=None, , keep=None)

Delete cached cubes, optionally keeping a set of keys. Returns what went.

There is no eviction policy and this is not one — it is the caller’s own
decision, made explicit. Every entry is reproducible from its key, so
deleting all of them is always safe; the only cost is regenerating, at
0.141 s per 33-cube.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.terms_for(provider, realisation=None, component=None)

Every ledger row matching a provider, optionally narrowed.

Returns **all** matching components, because a provider is assessed by its
worst one and handing back a single row would be the per-package key the
ledger deliberately does not have.

### Examples

```pycon
>>> [t.component for t in terms_for('moviepy')]
['code', 'transitive']
>>> assess(terms_for('moviepy')).tier
<Tier.COPYLEFT_SHIPPED: 'copyleft_shipped'>
>>> terms_for('no-such-provider')
()
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Terms`](looks.licence.html.md#looks.licence.Terms), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.unmet_filters(plan, env)

Filters this plan needs that this binary does not have.

Separate from [`audit()`](#looks.audit) on purpose: a licence refusal is about what a
caller may do, and a missing filter is about what a machine can do. They
fail for different reasons, are fixed by different people, and collapsing
them produces a message that helps neither.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.unverified_claims()

What the research explicitly did **not** establish.

Recorded rather than omitted: an unverified claim asserted as fact defeats
the point of the whole design, and the claims here are the ones somebody
will otherwise assume were checked.

### Examples

```pycon
>>> len(unverified_claims()) >= 4
True
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.vf(plan, , gate=True)

A whole plan as one `-vf` fragment: input-index-free, splice-ready.

The seam every consumer asked for is one string — `muvid` splices it into
the filter chain `_render_part` already builds, and that only works if
nothing here names a stream.

* **Raises:**
  [**FfmpegBackendError**](#looks.FfmpegBackendError) – If a step is not ffmpeg-backed, or is gated to a
      span its filter cannot honour. The second is why
      [`timeline`](looks.spec.html.md#looks.spec.ImplRef.timeline) exists: `zoompan` and
      `elbg` carry no timeline support, so an `at` on them would be
      accepted by the string and ignored by the binary.
* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### looks.write_cube(spec, path, , size=33, title='looks_gradient_map')

Write the `.cube` for `spec` to `path` and return it.

Creates parent directories. Writing is not conditional on the file’s
absence — the caller owns the cache policy, and this owns the bytes.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### looks.xfade_options(transition, , offset, fps=None, first_clip_s=None)

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

### looks.zoompan_fragment(keyframes, , output, fps, aspect_tolerance=1e-06)

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
  [**MotionError**](#looks.MotionError) – If any window is not geometrically similar to the source
      frame. `zoom` is a single scalar, so the visible region is always
      `(iw/zoom, ih/zoom)` — one axis cannot be zoomed differently from
      the other, and honouring one while distorting the other silently is
      the failure this refuses.
* **Return type:**
  [*str*](https://docs.python.org/3/builtins/stdtypes.html#str)

### Modules

| [`across`](looks.across.html.md#module-looks.across)                     | Choosing one parameter per clip so a SET looks consistent — exactly, not by search.   |
|-------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| [`cache`](looks.cache.html.md#module-looks.cache)                       | A `.cube` is a build artifact.                                                        |
| [`cli`](looks.cli.html.md#module-looks.cli)                           | The command line: thin adapters over the library, and no logic of its own.            |
| [`compile`](looks.compile.html.md#module-looks.compile)                   | A Look plus a clip plus a binary, compiled into a plan — and re-checked.              |
| [`environment`](looks.environment.html.md#module-looks.environment)           | What the ffmpeg on *this* machine actually is, and what it can actually do.           |
| [`ffmpeg`](looks.ffmpeg.html.md#module-looks.ffmpeg)                     | The ffmpeg backend: filter strings, escaping, and the first effects.                  |
| [`frame_dependency`](looks.frame_dependency.html.md#module-looks.frame_dependency) | Can this effect flicker? Answered by measurement, not by judgement.                   |
| [`geometry`](looks.geometry.html.md#module-looks.geometry)                 | Where a source frame lands inside a target frame.                                     |
| [`licence`](looks.licence.html.md#module-looks.licence)                   | What an implementation costs you in obligations, and when to refuse it.               |
| [`lut`](looks.lut.html.md#module-looks.lut)                           | Gradient-map 3D LUTs: a colour ramp in, an Iridas `.cube` out.                        |
| [`motion`](looks.motion.html.md#module-looks.motion)                     | A camera path, compiled to an ffmpeg fragment — the compile half of RULE G.           |
| [`pipe`](looks.pipe.html.md#module-looks.pipe)                         | A plan that mixes backends, as a pipe — emitted as data, never spawned.               |
| [`registry`](looks.registry.html.md#module-looks.registry)                 | Which implementations exist, and how to reach the code behind a plan.                 |
| [`spec`](looks.spec.html.md#module-looks.spec)                         | What a stylization *is*, before anything runs.                                        |
| [`transition`](looks.transition.html.md#module-looks.transition)             | How one shot gives way to the next — the vocabulary, not the graph.                   |
