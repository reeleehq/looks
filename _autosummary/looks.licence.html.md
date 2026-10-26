# looks.licence

What an implementation costs you in obligations, and when to refuse it.

This is the module the package exists for. Everything else in `looks`
computes a filter string; this decides whether you are allowed to run it.

**looks reports observations, not legal conclusions.**

A tier is not a legal determination. It is a position on a policy ladder this
project chose, derived from things that were mechanically observed on a stated
date — a command that was run, a file that was read, a binary that was
interrogated — and every row records that observation so you can check the
derivation rather than trust the label.

looks refuses when it cannot observe. It does not adjudicate: where an
artifact’s own statements about itself disagree, looks reports the
disagreement and refuses, and does not decide which statement is true.

Raising a ceiling is a decision about *your* obligations, not about this
software’s. Whether the licences and terms recorded here permit what you
intend to do is a question for you and your counsel.

## The shape

**The facts are four orthogonal axes** — [`Coupling`](#looks.licence.Coupling), [`Reach`](#looks.licence.Reach),
[`Conveyance`](#looks.licence.Conveyance), [`FieldOfUse`](#looks.licence.FieldOfUse) — recorded on [`Terms`](#looks.licence.Terms), which an
implementation declares about itself. \*An implementation declares terms, never
a tier.\* A frozen `tier=` field would be wrong twice over: it is a false
refusal for the LGPL-clean majority of ffmpeg’s colour vocabulary, and it
cannot distinguish the one filter (`eq`) that genuinely is GPL-only. The
same effect is `Tier.WEAK_COPYLEFT` on an LGPL ffmpeg and
`Tier.COPYLEFT_TOOL` on a GPL one, so the tier is *resolved* at compile
time by [`classify()`](#looks.licence.classify), from what the implementation declared joined with
what the environment turned out to be.

**The ladder is a replaceable policy projection of three of those axes**, not a
fact about licences — which is why the function that computes it is called
[`project_onto_ladder()`](#looks.licence.project_onto_ladder) and the shipped ordering is
[`DFLT_LADDER`](#looks.licence.DFLT_LADDER), a default on [`Policy`](#looks.licence.Policy) rather than a constant of
the domain. Rungs 2 and 3 are *not* ordered by obligation-inclusion: in-process
LGPL and subprocess GPL impose different duties, not more and fewer, and plenty
of corporate policies rank them the other way. The shipped order is chosen for
what this federation ships — Python source that shells out and bundles nothing.
A caller with a different posture passes `Policy(order=...)`.

\*\*Three regions are off the ladder, where no `max_tier` reaches them.\*\*
`Verdict.FORBIDDEN` (in-process strong copyleft, plus any recorded
prohibition), `Verdict.FIELD_RESTRICTED` (non-commercial, research-only)
and `Verdict.UNKNOWN`. Field of use is *not commensurable* with copyleft
strength — a non-commercial model is not “more copyleft than GPL”, it is a
different kind of failure — so a ladder that admits it when you raise the
ceiling one notch is a trap, and so is a rung you can opt into for something
the design says to “always refuse”.

**\`\`max_tier\`\` is not the commercial-safe knob.** Every rung, including
`Tier.COPYLEFT_SHIPPED`, is commercially usable — a source offer is a
duty, not a prohibition. What is *not* commercially usable is
`FieldOfUse.NON_COMMERCIAL`, which is off the ladder. So
“commercial-safe only” is `allow_field_restricted=frozenset()`, which is
already the default. Advertise it as `max_tier` and the promise and the
semantics drift apart on day one.

## What this module does not restate

Two questions belong to [`looks.environment`](looks.environment.html.md#module-looks.environment) and are consumed from it
rather than duplicated here: *which ffmpeg filters are GPL-gated*
(`needs_gpl`, over the committed `ffmpeg_gates.json`) and \*what licence
does this binary carry\* (`probe` -> `FfmpegEnv.licence`, from `ffmpeg
-L`). A second copy of either is how two detectors start disagreeing.
[`ffmpeg_terms()`](#looks.licence.ffmpeg_terms) and [`assess_ffmpeg_chain()`](#looks.licence.assess_ffmpeg_chain) are the joins.

```pycon
>>> env = FfmpegEnv(path='/opt/homebrew/bin/ffmpeg', licence=Licence.GPL3,
...                 filters=frozenset({'lut3d', 'lutrgb', 'eq'}))
>>> classify(ffmpeg_terms(env)).tier
<Tier.COPYLEFT_TOOL: 'copyleft_tool'>
```

### Module Attributes

| [`SPDX_LICENSE_LIST_VERSION`](#looks.licence.SPDX_LICENSE_LIST_VERSION)   | The SPDX License List release [`REACH_BY_SPDX`](#looks.licence.REACH_BY_SPDX) is written against.                                                                                           |
|------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| [`STALE_AFTER_DAYS`](#looks.licence.STALE_AFTER_DAYS)            | Days after which a ledger row's evidence is *reported* stale.                                                                                                                                              |
| [`LEDGER_PATH`](#looks.licence.LEDGER_PATH)                 | The evidence ledger, one row per `(provider, realisation, component)`.                                                                                                                                     |
| [`LEDGER_SCHEMA`](#looks.licence.LEDGER_SCHEMA)               | Its schema tag.                                                                                                                                                                                            |
| [`SEE_DISCLAIMER`](#looks.licence.SEE_DISCLAIMER)              | The one-line pointer a refusal carries.                                                                                                                                                                    |
| [`RESTRICTED_FIELDS`](#looks.licence.RESTRICTED_FIELDS)           | The field-of-use values that are a restriction rather than an absence of one.                                                                                                                              |
| [`STRONG_COPYLEFT`](#looks.licence.STRONG_COPYLEFT)             | The reaches that put an in-process implementation in the forbidden region.                                                                                                                                 |
| [`REACH_BY_SPDX`](#looks.licence.REACH_BY_SPDX)               | SPDX identifier -> copyleft [`Reach`](#looks.licence.Reach).                                                                                                                        |
| [`EXCLUDED_SPDX`](#looks.licence.EXCLUDED_SPDX)               | Identifiers left out of [`REACH_BY_SPDX`](#looks.licence.REACH_BY_SPDX) on purpose, with the reason.                                                                                        |
| [`DFLT_LADDER`](#looks.licence.DFLT_LADDER)                 | The shipped ladder, lowest rung first — a **default on** [`Policy`](#looks.licence.Policy), not a constant of the domain.                                                            |
| [`DFLT_MAX_TIER`](#looks.licence.DFLT_MAX_TIER)               | "Shelling out to a copyleft binary is fine", stated precisely.                                                                                                                                             |
| [`DFLT_POLICY`](#looks.licence.DFLT_POLICY)                 | shell out to a copyleft binary freely, convey nothing, and accept no field-of-use restriction.                                                                                                             |
| [`SPDX_BY_FFMPEG_LICENCE`](#looks.licence.SPDX_BY_FFMPEG_LICENCE)      | What `ffmpeg -L` reports, as an SPDX identifier.                                                                                                                                                           |
| [`NONFREE_PROHIBITION`](#looks.licence.NONFREE_PROHIBITION)         | The nonfree refusal, recorded as a prohibition so it is checked **before** any ceiling comparison and cannot be folded into UNKNOWN — whose remedy text is "supply evidence", which is exactly wrong here. |
| [`KNOWN_COMPONENTS`](#looks.licence.KNOWN_COMPONENTS)            | The component vocabulary the ledger is validated against.                                                                                                                                                  |
| [`KNOWN_REALISATION_PREFIXES`](#looks.licence.KNOWN_REALISATION_PREFIXES)  | How a row may say where the thing came from.                                                                                                                                                               |

### Functions

| [`reach_of`](#looks.licence.reach_of)(spdx)                                | Map one SPDX identifier onto a [`Reach`](#looks.licence.Reach).   |
|------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------|
| [`project_onto_ladder`](#looks.licence.project_onto_ladder)(terms)                    | Project three axes onto a rung.                                                          |
| [`classify`](#looks.licence.classify)(terms, \*[, today])                  | Locate `terms` in the axis space.                                                        |
| [`assess`](#looks.licence.assess)(terms, \*[, order, today])             | Assess a provider made of several components: **the worst one wins.**                    |
| [`check`](#looks.licence.check)(assessment, policy, subject, \*[, ...]) | Raise unless `policy` admits `assessment`.                                               |
| [`ffmpeg_terms`](#looks.licence.ffmpeg_terms)(env, \*[, realisation, today])   | One probed ffmpeg binary, as [`Terms`](#looks.licence.Terms).     |
| [`assess_ffmpeg_chain`](#looks.licence.assess_ffmpeg_chain)(filters, \*, env[, ...])  | The licence position of a filter chain on one probed binary.                             |
| [`ledger`](#looks.licence.ledger)()                                      | The evidence ledger: what was observed, about whom, and when.                            |
| [`terms_for`](#looks.licence.terms_for)(provider[, realisation, component]) | Every ledger row matching a provider, optionally narrowed.                               |
| [`unverified_claims`](#looks.licence.unverified_claims)()                           | What the research explicitly did **not** establish.                                      |

### Classes

| [`Coupling`](#looks.licence.Coupling)(\*values)                                 | How the implementation is reached — whether copyleft can touch us.                    |
|-----------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------------|
| [`Reach`](#looks.licence.Reach)(\*values)                                    | How far the implementation's copyleft extends.                                        |
| [`Conveyance`](#looks.licence.Conveyance)(\*values)                               | Whether a *declared dependency closure* ships the implementation.                     |
| [`FieldOfUse`](#looks.licence.FieldOfUse)(\*values)                               | Whether the *purpose* is permitted.                                                   |
| [`Tier`](#looks.licence.Tier)(\*values)                                     | A rung on a ladder that is **policy, not fact**.                                      |
| [`Verdict`](#looks.licence.Verdict)(\*values)                                  | Which region of the axis space the terms landed in.                                   |
| [`Patent`](#looks.licence.Patent)(\*, patent_id, jurisdiction[, holder, ...]) | A patent encumbrance, which no copyright vocabulary can express.                      |
| [`Evidence`](#looks.licence.Evidence)(\*, method, observed, observed_on[, ...]) | One observation, with enough context to be re-checked or disbelieved.                 |
| [`Terms`](#looks.licence.Terms)(\*, provider, realisation, spdx, coupling)   | What one component declares about itself.                                             |
| [`Assessment`](#looks.licence.Assessment)(\*, terms, tier, verdict[, ...])        | Where [`classify()`](#looks.licence.classify) located some terms. |
| [`Policy`](#looks.licence.Policy)(\*[, max_tier, ...])                        | A ceiling, plus the thing a ceiling deliberately cannot reach.                        |

### Exceptions

| [`LooksLicenceError`](#looks.licence.LooksLicenceError)      | Base for every licence refusal.                     |
|-------------------------------------------------------------------------|-----------------------------------------------------|
| [`LicenceCeilingExceeded`](#looks.licence.LicenceCeilingExceeded) | On the ladder, above the ceiling.                   |
| [`LicenceForbidden`](#looks.licence.LicenceForbidden)       | Off the ladder, permanently.                        |
| [`LicenceFieldRestricted`](#looks.licence.LicenceFieldRestricted) | Non-commercial / research-only / no-derivatives.    |
| [`LicenceUnknown`](#looks.licence.LicenceUnknown)         | Undeterminable, unprobeable, or self-contradictory. |

### *class* looks.licence.Assessment(, terms, tier, verdict, reasons=(), advisories=(), parts=())

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Where [`classify()`](#looks.licence.classify) located some terms. Not a permission.

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

#### parts *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[Assessment](#looks.licence.Assessment), ...]*

The per-component assessments when this came from [`assess()`](#looks.licence.assess).
[`check()`](#looks.licence.check) applies the ceiling to **every** part, so a composite
cannot admit something one of its components would not.

#### *property* severity *: [int](https://docs.python.org/3/builtins/functions.html#int)*

Rank in `_VERDICT_SEVERITY`; higher is louder.

### *class* looks.licence.Conveyance(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Whether a *declared dependency closure* ships the implementation.

Whose closure is the load-bearing word. A caller’s pre-existing
`imageio-ffmpeg` is `FINDS` — `looks` does not declare it and
does not convey it. It becomes `CONVEYS` for whoever *does* declare
it, which is why a ledger row is keyed on how you obtain the thing rather
than on the thing: `realisation="system"` finds, `realisation="pypi:x"`
describes the position of a package that declares `x`.

### *class* looks.licence.Coupling(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How the implementation is reached — whether copyleft can touch us.

This axis and [`Conveyance`](#looks.licence.Conveyance) are the two that separate the four cases
people habitually conflate: executing a copyleft program you found
(`SUBPROCESS` + `FINDS`), executing one you shipped (`+ CONVEYS`),
linking one (`IN_PROCESS`), and calling a hosted one (`SERVICE`).

### looks.licence.DFLT_LADDER *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[Tier](#looks.licence.Tier), ...]* *= (Tier.PURE, Tier.PERMISSIVE, Tier.WEAK_COPYLEFT, Tier.COPYLEFT_TOOL, Tier.COPYLEFT_SHIPPED)*

The shipped ladder, lowest rung first — a **default on** [`Policy`](#looks.licence.Policy),
not a constant of the domain. Chosen for what this federation ships: Python
source that shells out and bundles nothing, where the question that matters
is “does copyleft touch our source” and rung 3 answers “no, unless you later
ship the tool”. Pass your own to reorder it.

### looks.licence.DFLT_MAX_TIER *= Tier.COPYLEFT_TOOL*

“Shelling out to a copyleft binary is fine”, stated precisely.

### looks.licence.DFLT_POLICY *= Policy(max_tier=<Tier.COPYLEFT_TOOL: 'copyleft_tool'>, allow_field_restricted=frozenset(), order=(<Tier.PURE: 'pure'>, <Tier.PERMISSIVE: 'permissive'>, <Tier.WEAK_COPYLEFT: 'weak_copyleft'>, <Tier.COPYLEFT_TOOL: 'copyleft_tool'>, <Tier.COPYLEFT_SHIPPED: 'copyleft_shipped'>))*

shell out to a copyleft binary freely, convey nothing,
and accept no field-of-use restriction.

* **Type:**
  The shipped ceiling

### looks.licence.EXCLUDED_SPDX *: [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [str](https://docs.python.org/3/builtins/stdtypes.html#str)]* *= {'BSD-4-Clause': 'the advertising clause is a real obligation, and the text is word-for-word BSD-3-Clause plus one paragraph — so it must be excluded explicitly or it gets waved through as BSD'}*

Identifiers left out of [`REACH_BY_SPDX`](#looks.licence.REACH_BY_SPDX) on purpose, with the reason.
Recorded rather than merely omitted, because an absence looks identical to
an oversight and someone eventually “fixes” it.

### *class* looks.licence.Evidence(, method, observed, observed_on, command=None, source_url=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

One observation, with enough context to be re-checked or disbelieved.

#### is_stale(, today=None)

Older than [`STALE_AFTER_DAYS`](#looks.licence.STALE_AFTER_DAYS). Reported, never auto-refused.

### Examples

```pycon
>>> old = Evidence(method="read", observed="x",
...                observed_on="2020-01-01")
>>> old.is_stale(today=date(2026, 9, 2))
True
>>> Evidence(method="read", observed="x", observed_on="2026-09-02"
...          ).is_stale(today=date(2026, 9, 2))
False
```

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### *class* looks.licence.FieldOfUse(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Whether the *purpose* is permitted. Orthogonal to every axis above.

No SPDX identifier carries this, so it is always a declared column and is
never parsed out of a licence id: `CC-BY-NC-SA-4.0` is a listed
identifier whose non-commercial character is not derivable from the string,
and AnimeGANv2’s terms have no identifier at all.

### looks.licence.KNOWN_COMPONENTS *: [frozenset](https://docs.python.org/3/builtins/stdtypes.html#frozenset)[[str](https://docs.python.org/3/builtins/stdtypes.html#str)]* *= frozenset({'assets', 'binary', 'bundled-ffmpeg', 'code', 'model', 'transitive', 'weights'})*

The component vocabulary the ledger is validated against. Closed on purpose:
`code` and `weights` being separate rows is what keeps a permissively
licensed port of non-permissive weights from reading as permissive.

### looks.licence.KNOWN_REALISATION_PREFIXES *: [tuple](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), ...]* *= ('system', 'self', 'any', 'pypi:', 'github:', 'weights:', 'hosted:', 'commercial:')*

How a row may say where the thing came from. `@` separates a platform,
because a wheel’s tier is a property of the wheel: one distribution name
covers three different answers across macOS arm64, macOS x86_64 and
manylinux.

### looks.licence.LEDGER_PATH *= PosixPath('/home/runner/work/looks/looks/looks/data/provider_terms.json')*

The evidence ledger, one row per `(provider, realisation, component)`.

### looks.licence.LEDGER_SCHEMA *= 'looks.provider_terms/v1'*

Its schema tag. An unrecognised tag is refused loudly.

### *exception* looks.licence.LicenceCeilingExceeded

Bases: [`LooksLicenceError`](#looks.licence.LooksLicenceError)

On the ladder, above the ceiling. Raise it, or pick a lower provider.

### *exception* looks.licence.LicenceFieldRestricted

Bases: [`LooksLicenceError`](#looks.licence.LooksLicenceError)

Non-commercial / research-only / no-derivatives. Its OWN opt-in.

### *exception* looks.licence.LicenceForbidden

Bases: [`LooksLicenceError`](#looks.licence.LooksLicenceError)

Off the ladder, permanently. There is no opt-in and no ceiling.

### *exception* looks.licence.LicenceUnknown

Bases: [`LooksLicenceError`](#looks.licence.LooksLicenceError)

Undeterminable, unprobeable, or self-contradictory. Unknown refuses.

### *exception* looks.licence.LooksLicenceError

Bases: [`Exception`](https://docs.python.org/3/builtins/exceptions.html#Exception)

Base for every licence refusal.

### looks.licence.NONFREE_PROHIBITION *= "FFmpeg calls this build nonfree and unredistributable. That is the project's own characterisation of it, not an inference, and no evidence lifts it. The incremental capability is nil for this package in any case: libfdk_aac and libmpeghdec are audio, decklink is capture hardware, and the libnpp filters have LGPL equivalents in unsharp and convolution."*

The nonfree refusal, recorded as a prohibition so it is checked **before**
any ceiling comparison and cannot be folded into UNKNOWN — whose remedy text
is “supply evidence”, which is exactly wrong here. FFmpeg’s own words for
such a build are “nonfree and unredistributable”, which is the
best-characterised refusal available and one no evidence can lift.

### *class* looks.licence.Patent(, patent_id, jurisdiction, holder='', status='unknown', expiry=None, source_url=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

A patent encumbrance, which no copyright vocabulary can express.

Forced into existence by one row: Ebsynth is *public-domain code*
implementing Adobe’s PatchMatch (US8861869B2, Active, anticipated expiry
2030-08-16). Public domain is the most permissive value any copyright
vocabulary has, and for that artifact it is the wrong answer.

`looks` **records a patent and reports it; it never refuses on it.** A
patent binds an act in a jurisdiction rather than a redistribution, and
deciding whether it binds *your* act is the adjudication the honesty rule
forbids. What it may not do is be invisible — see
[`Assessment.advisories`](#looks.licence.Assessment.advisories).

#### is_live(, today=None)

Whether it is still, or might still be, in force.

Unknown expiry counts as live. Unknown is not permission here either.

### Examples

```pycon
>>> ebsynth = Patent(patent_id="US8861869B2", jurisdiction="US",
...                  status="active", expiry="2030-08-16")
>>> ebsynth.is_live(today=date(2026, 9, 2))
True
>>> ebsynth.is_live(today=date(2031, 1, 1))
False
>>> Patent(patent_id="?", jurisdiction="US").is_live()
True
```

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### *class* looks.licence.Policy(, max_tier=Tier.COPYLEFT_TOOL, allow_field_restricted=frozenset({}), order=(Tier.PURE, Tier.PERMISSIVE, Tier.WEAK_COPYLEFT, Tier.COPYLEFT_TOOL, Tier.COPYLEFT_SHIPPED))

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

#### allow_field_restricted *: [frozenset](https://docs.python.org/3/builtins/stdtypes.html#frozenset)[[FieldOfUse](#looks.licence.FieldOfUse)]*

Which field-of-use restrictions the caller has deliberately accepted.
Empty by default, and **never** widened by `max_tier`.

#### rank(tier)

Position on *this* policy’s ladder.

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

### looks.licence.REACH_BY_SPDX *: [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[str](https://docs.python.org/3/builtins/stdtypes.html#str), [Reach](#looks.licence.Reach)]* *= {'0BSD': Reach.NONE, 'AGPL-3.0-only': Reach.NETWORK, 'AGPL-3.0-or-later': Reach.NETWORK, 'Apache-2.0': Reach.NONE, 'BSD-2-Clause': Reach.NONE, 'BSD-3-Clause': Reach.NONE, 'BlueOak-1.0.0': Reach.NONE, 'CC0-1.0': Reach.NONE, 'CDDL-1.0': Reach.FILE, 'EPL-2.0': Reach.FILE, 'GPL-2.0-only': Reach.PROGRAM, 'GPL-2.0-or-later': Reach.PROGRAM, 'GPL-3.0-only': Reach.PROGRAM, 'GPL-3.0-or-later': Reach.PROGRAM, 'ISC': Reach.NONE, 'LGPL-2.1-only': Reach.LIBRARY, 'LGPL-2.1-or-later': Reach.LIBRARY, 'LGPL-3.0-only': Reach.LIBRARY, 'LGPL-3.0-or-later': Reach.LIBRARY, 'MIT': Reach.NONE, 'MIT-0': Reach.NONE, 'MPL-2.0': Reach.FILE, 'Python-2.0': Reach.NONE, 'SSPL-1.0': Reach.PROGRAM, 'Unlicense': Reach.NONE}*

SPDX identifier -> copyleft [`Reach`](#looks.licence.Reach). SPDX is the vocabulary; the axes
are ours, because SPDX encodes none of them — it cannot say whether you
linked or executed, whether you shipped or found, or whether the field of
use is restricted. Anything unlisted is `Reach.UNKNOWN`, which
refuses, in both directions. Widening this table is a dated decision, never
a convenience.

### looks.licence.RESTRICTED_FIELDS *: [frozenset](https://docs.python.org/3/builtins/stdtypes.html#frozenset)[[FieldOfUse](#looks.licence.FieldOfUse)]* *= frozenset({FieldOfUse.NON_COMMERCIAL, FieldOfUse.NO_DERIVATIVES, FieldOfUse.RESEARCH_ONLY})*

The field-of-use values that are a restriction rather than an absence of
one. `FieldOfUse.UNKNOWN` is deliberately absent: “we do not know what
this restricts” is an unknown, and folding it in here would let a caller opt
into it, which is laundering unknown into permission.

### *class* looks.licence.Reach(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

How far the implementation’s copyleft extends.

### looks.licence.SEE_DISCLAIMER *= 'looks reports observations, not legal conclusions — see looks.licence.DISCLAIMER.'*

The one-line pointer a refusal carries. The full `DISCLAIMER` on every
raise becomes noise, and noise is how a disclaimer stops being read.

### looks.licence.SPDX_BY_FFMPEG_LICENCE *: [Mapping](https://docs.python.org/3/library/typing.html#typing.Mapping)[[Licence](looks.environment.html.md#looks.environment.Licence), [str](https://docs.python.org/3/builtins/stdtypes.html#str)]* *= {Licence.GPL2: 'GPL-2.0-or-later', Licence.GPL3: 'GPL-3.0-or-later', Licence.LGPL21: 'LGPL-2.1-or-later', Licence.LGPL3: 'LGPL-3.0-or-later'}*

What `ffmpeg -L` reports, as an SPDX identifier. “or-later” throughout,
because FFmpeg’s own cascade says “version N, or (at your option) any later
version”. `Licence.NONFREE` and `Licence.UNKNOWN` are absent on
purpose: neither is a licence position, and each refuses differently.

### looks.licence.SPDX_LICENSE_LIST_VERSION *= '3.28.0'*

The SPDX License List release [`REACH_BY_SPDX`](#looks.licence.REACH_BY_SPDX) is written against.
Recorded because the mapping is only as current as the list it was read
from, and a widened row is a dated decision.

### looks.licence.STALE_AFTER_DAYS *= 365*

Days after which a ledger row’s evidence is *reported* stale. Deliberately
never an automatic refusal: staleness is not a licence fact, refusing on it
would stop the package working offline for a non-licence reason, and a
refusal nobody can act on is the one people delete.

### looks.licence.STRONG_COPYLEFT *: [frozenset](https://docs.python.org/3/builtins/stdtypes.html#frozenset)[[Reach](#looks.licence.Reach)]* *= frozenset({Reach.NETWORK, Reach.PROGRAM})*

The reaches that put an in-process implementation in the forbidden region.

### *class* looks.licence.Terms(, provider, realisation, spdx, coupling, component='code', conveyance=Conveyance.UNKNOWN, field_of_use=FieldOfUse.UNKNOWN, reach=None, patents=(), conditions=(), prohibition=None, contradiction=None, verified=True, evidence=(), note='')

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

#### reach *: [Optional](https://docs.python.org/3/library/typing.html#typing.Optional)[[Reach](#looks.licence.Reach)]*

Override the [`Reach`](#looks.licence.Reach) derived from `spdx`. Requires a
`note`, because an unexplained override silently makes a row the
most permissive of its available readings — which is how a compound
`"Apache-2.0 AND GPL-3.0-or-later"` row once classified PERMISSIVE.

#### *property* resolved_reach *: [Reach](#looks.licence.Reach)*

The declared reach, or the one [`reach_of()`](#looks.licence.reach_of) derives.

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

### *class* looks.licence.Tier(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

A rung on a ladder that is **policy, not fact**.

Deliberately a plain [`enum.Enum`](https://docs.python.org/3/library/enum.html#enum.Enum) with no ordering of its own, so
`<` cannot silently mean the shipped ladder when a caller supplied a
different one. Ranking goes through [`Policy.rank()`](#looks.licence.Policy.rank).

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

### *class* looks.licence.Verdict(\*values)

Bases: [`Enum`](https://docs.python.org/3/library/enum.html#enum.Enum)

Which region of the axis space the terms landed in.

`ON_LADDER` is **not** “admitted”. [`classify()`](#looks.licence.classify) locates terms; it
does not apply a ceiling, and reading `ON_LADDER` as permission is the
false-permission direction. [`check()`](#looks.licence.check) is what admits or refuses.

The other three are the regions no `max_tier` reaches, kept apart because
their remedies genuinely differ: raise the ceiling, no opt-in exists, a
separate opt-in, supply evidence.

### looks.licence.assess(terms, , order=(Tier.PURE, Tier.PERMISSIVE, Tier.WEAK_COPYLEFT, Tier.COPYLEFT_TOOL, Tier.COPYLEFT_SHIPPED), today=None)

Assess a provider made of several components: **the worst one wins.**

Deliberately *not* a per-axis join. Join OpenCV’s Apache-2.0 in-process C++
with the GPL ffmpeg conveyed in the same wheel and you get “we link a GPL
program in-process” — a chimera true of neither component, which then
classifies FORBIDDEN. Each component keeps its own row, the caller sees
which half is the problem, and [`check()`](#looks.licence.check) applies the ceiling to \*\*every
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
  [`Assessment`](#looks.licence.Assessment)

### looks.licence.assess_ffmpeg_chain(filters, , env, realisation='system', today=None)

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
  [`Assessment`](#looks.licence.Assessment)

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

### looks.licence.check(assessment, policy, subject, , alternatives=())

Raise unless `policy` admits `assessment`. Returns `None` on pass.

Every component is checked, loudest first, so a composite can never admit
something one of its parts would not — and so the message names the
component that is actually the problem.

A refusal message names, in order: the subject, the tier it needs, the
ceiling in force, *why* (the resolved provider and the dated observations
that decided it), how to opt in, and any lower-tier alternative. A refusal
that only says no is the one people remove.

* **Parameters:**
  * **assessment** ([`Assessment`](#looks.licence.Assessment)) – From [`classify()`](#looks.licence.classify) or [`assess()`](#looks.licence.assess).
  * **policy** ([`Policy`](#looks.licence.Policy)) – The ceiling in force, plus any field-of-use opt-in.
  * **subject** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str)) – What is being refused — an effect name, an implementation id.
  * **alternatives** ([`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]) – Lower-tier implementations of the same capability, named
    in the message.
* **Raises:**
  * [**LicenceForbidden**](#looks.licence.LicenceForbidden) – Off the ladder permanently; no opt-in exists.
  * [**LicenceUnknown**](#looks.licence.LicenceUnknown) – Undeterminable, unverified, or self-contradictory.
  * [**LicenceFieldRestricted**](#looks.licence.LicenceFieldRestricted) – Restricted purpose, and no opt-in was given.
  * [**LicenceCeilingExceeded**](#looks.licence.LicenceCeilingExceeded) – On the ladder, above the ceiling.
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

### looks.licence.classify(terms, , today=None)

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
  [`Assessment`](#looks.licence.Assessment)

### looks.licence.ffmpeg_terms(env, , realisation='system', today=None)

One probed ffmpeg binary, as [`Terms`](#looks.licence.Terms).

**The environment is an argument.** This takes an `FfmpegEnv` a
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
    what decides [`Conveyance`](#looks.licence.Conveyance), and therefore rung 3 versus 4.
  * **today** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`date`](https://docs.python.org/3/library/datetime.html#datetime.date)]) – Stamped on the evidence; for tests.
* **Return type:**
  [`Terms`](#looks.licence.Terms)

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

### looks.licence.ledger()

The evidence ledger: what was observed, about whom, and when.

**No tier is stored.** Every row records axes and the dated observations
behind them; the tier comes from [`classify()`](#looks.licence.classify), so a reader can check
the derivation rather than trust a label — and the test suite re-derives
every row. Rows are keyed per component, because the compound cases
(OpenCV, moviepy) cannot round-trip through a per-package key.

It is a record of observations, **not a lookup table for a live machine**.
In particular, do not read the `ffmpeg`/`system` row to decide what a
caller’s ffmpeg is: use [`ffmpeg_terms()`](#looks.licence.ffmpeg_terms) on an
[`FfmpegEnv`](looks.environment.html.md#looks.environment.FfmpegEnv) they probed.

### Examples

```pycon
>>> rows = ledger()
>>> len(rows) > 25
True
>>> sorted({t.provider for t in rows})[:4]
['adobe-lut-packs', 'anime4k', 'animegan2-pytorch', 'animeganv2']
```

The tier is derived, and the compound case is why:

```pycon
>>> opencv = terms_for('opencv')
>>> classify(next(t for t in opencv if t.component == 'code')).tier
<Tier.PERMISSIVE: 'permissive'>
>>> assess(opencv).verdict
<Verdict.UNKNOWN: 'unknown'>
```

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Terms`](#looks.licence.Terms), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.licence.project_onto_ladder(terms)

Project three axes onto a rung. **This is the policy half.**

Coupling, reach and conveyance go in; a rung or `None` comes out.
[`FieldOfUse`](#looks.licence.FieldOfUse) is deliberately not consulted — it is not commensurable
with copyleft strength and belongs off the ladder entirely.

`None` means *no rung*: an axis is unknown, or the terms are in the
forbidden region. Which of the two it is, is [`classify()`](#looks.licence.classify)’s answer.

Note what conveyance does and does not do. It lifts rung 3 to rung 4 —
conveying a GPL *program* is a source-offer duty you inherit — and it does
nothing anywhere else, because that is the ladder as decided. (Section 5.7
of the decisions document contains one row on the other side of this, the
vendored LGPL shaders; its own manylinux-wheel row contradicts it, and both
cannot hold under one projection.)

### Examples

```pycon
>>> found = Terms(provider="ffmpeg", realisation="system",
...               spdx="GPL-3.0-or-later", component="binary",
...               coupling=Coupling.SUBPROCESS,
...               conveyance=Conveyance.FINDS,
...               field_of_use=FieldOfUse.UNRESTRICTED)
>>> project_onto_ladder(found)
<Tier.COPYLEFT_TOOL: 'copyleft_tool'>
```

The same binary, shipped inside a wheel you declare:

```pycon
>>> project_onto_ladder(
...     Terms(provider="ffmpeg", realisation="pypi:imageio-ffmpeg",
...           spdx="GPL-2.0-or-later", component="binary",
...           coupling=Coupling.SUBPROCESS,
...           conveyance=Conveyance.CONVEYS,
...           field_of_use=FieldOfUse.UNRESTRICTED))
<Tier.COPYLEFT_SHIPPED: 'copyleft_shipped'>
```

And linked instead of executed, which is off the ladder:

```pycon
>>> project_onto_ladder(
...     Terms(provider="ultralytics", realisation="pypi:ultralytics",
...           spdx="AGPL-3.0-or-later", coupling=Coupling.IN_PROCESS,
...           conveyance=Conveyance.CONVEYS,
...           field_of_use=FieldOfUse.UNRESTRICTED)) is None
True
```

* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Tier`](#looks.licence.Tier)]

### looks.licence.reach_of(spdx)

Map one SPDX identifier onto a [`Reach`](#looks.licence.Reach).

Compound expressions are **not** parsed. A component needing `AND` or
`OR` is not one component: the conjunction that actually occurs — a
permissive library inside a wheel that also conveys a GPL program — is two
rows with two couplings, not one licence, and joining their axes
manufactures “we link a GPL program in-process”, a fact true of neither.

### Examples

```pycon
>>> reach_of("Apache-2.0")
<Reach.NONE: 'none'>
>>> reach_of("LGPL-3.0-or-later")
<Reach.LIBRARY: 'library'>
>>> reach_of("AGPL-3.0-or-later")
<Reach.NETWORK: 'network'>
```

Unlisted is unknown, which refuses — including the one that is unlisted
deliberately, and every `LicenseRef-*`:

```pycon
>>> reach_of("BSD-4-Clause")
<Reach.UNKNOWN: 'unknown'>
>>> reach_of("Apache-2.0 AND GPL-3.0-or-later")
<Reach.UNKNOWN: 'unknown'>
>>> reach_of("LicenseRef-AnimeGANv2-NonCommercial")
<Reach.UNKNOWN: 'unknown'>
```

* **Return type:**
  [`Reach`](#looks.licence.Reach)

### looks.licence.terms_for(provider, realisation=None, component=None)

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
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`Terms`](#looks.licence.Terms), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.licence.unverified_claims()

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
