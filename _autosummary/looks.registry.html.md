# looks.registry

Which implementations exist, and how to reach the code behind a plan.

A [`LookPlan`](looks.spec.html.md#looks.spec.LookPlan) holds no live callables — that is the whole
reason it can be serialised, diffed and hashed. The consequence is that
something has to turn a stored plan back into runnable work, and a stored plan
names its implementation by **key**. This module is what those keys point at.

\*\*A payload names a registry key and never a `module:attr` import path.\*\* A
plan is a document, documents arrive from places, and a document that can name
`os:system` is a remote-code-execution primitive wearing a schema tag. So the
only names that resolve are ones this process registered.

### A hand-rolled dict, declared as a deviation rather than discovered as one

The federation’s plugin pattern is `xdol.Registry`, and this is not it.
`xdol` depends on `dol`, and this package’s first non-negotiable is a
`pyproject.toml` declaring nothing but stdlib. So the *semantics* are adopted
— error on conflict, a reserved `tags` field — without the import. The
deviation is not novel: `burns.RENDER_BACKENDS` and `muvid.visualize._VISUALS`
are both plain dicts for the same reason. A consumer that wants tag search can
mirror this mapping into an `xdol.Registry` in one line.

### What is refused at registration, and why there

Two things, both of which would otherwise surface much later as a confusing
*absence*:

- **A duplicate implementation key.** Last-write-wins would silently change
  which code a stored plan resolves to, which is the one failure a
  content-addressed plan hash exists to prevent.
- **An ffmpeg implementation naming a filter that does not exist.** A typo
  makes [`select_impl()`](looks.spec.html.md#looks.spec.select_impl) drop the candidate on a set-inclusion
  test and report “no implementation available” — a refusal whose message
  points nowhere near the cause. This is D-2’s lesson applied one layer up:
  `needs_gpl` raises on an unrecognised filter rather than reporting it
  clean, and so does this.

A tier is **not** checked here. The registry records what exists; a
[`Policy`](looks.licence.html.md#looks.licence.Policy) refuses at selection. Registering a GPL
implementation is legitimate and necessary — refusing it at registration would
mean a caller with a GPL ceiling could not use one either.

### Module Attributes

| [`Compiler`](#looks.registry.Compiler)   | What a compiler is handed and what it must return.                       |
|-------------------------------------------------------------|--------------------------------------------------------------------------|
| [`CostFn`](#looks.registry.CostFn)     | What a cost estimator returns.                                           |
| [`KEY_SHAPE`](#looks.registry.KEY_SHAPE)  | The shape an implementation key must have, in words, for error messages. |
| [`REGISTRY`](#looks.registry.REGISTRY)   | The registry the compiler uses when not given another.                   |

### Functions

| [`effects`](#looks.registry.effects)()                                   | Every effect [`REGISTRY`](#looks.registry.REGISTRY) can serve.             |
|----------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------|
| [`get_compiler`](#looks.registry.get_compiler)(key)                           | The code behind a key, from [`REGISTRY`](#looks.registry.REGISTRY).        |
| [`get_impl`](#looks.registry.get_impl)(key)                               | The declaration behind a key, from [`REGISTRY`](#looks.registry.REGISTRY). |
| [`implementations`](#looks.registry.implementations)(effect)                     | What [`REGISTRY`](#looks.registry.REGISTRY) has for an effect.             |
| [`register_effect`](#looks.registry.register_effect)(impl, compiler, \*\*kwargs) | Register into [`REGISTRY`](#looks.registry.REGISTRY).                      |

### Classes

| [`EffectRegistry`](#looks.registry.EffectRegistry)([name])   | Effect name to implementations, and implementation key to code.   |
|---------------------------------------------------------------------------|-------------------------------------------------------------------|

### Exceptions

| [`ImplConflict`](#looks.registry.ImplConflict)   | That key is taken.                                                       |
|-----------------------------------------------------------------|--------------------------------------------------------------------------|
| [`RegistryError`](#looks.registry.RegistryError)  | A registration that would make a later refusal point at the wrong thing. |
| [`UnknownImpl`](#looks.registry.UnknownImpl)    | A plan names an implementation this process does not have.               |

### looks.registry.Compiler

What a compiler is handed and what it must return. The payload is
backend-shaped — see [`Step`](looks.spec.html.md#looks.spec.Step) — and must be plain data:
it is about to be hashed and serialised.

alias of `Callable`[[…], [`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### looks.registry.CostFn

What a cost estimator returns. `None` means **unknown**, never free — the
federation’s rule, and the reason this is a separate callable rather than a
number defaulting to 0.0.

alias of `Callable`[[…], [`float`](https://docs.python.org/3/builtins/functions.html#float) | [`None`](https://docs.python.org/3/builtins/constants.html#None)]

### *class* looks.registry.EffectRegistry(name='looks')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Effect name to implementations, and implementation key to code.

An instance rather than a module global, so a test can build its own and a
consumer can compose several. The module-level functions below delegate to
[`REGISTRY`](#looks.registry.REGISTRY), which is the one the compiler uses by default.

### Examples

```pycon
>>> from looks.licence import terms_for
>>> reg = EffectRegistry()
>>> impl = ImplRef(effect="lut3d", impl="lut3d.ffmpeg.default",
...                backend="ffmpeg", terms=terms_for("ffmpeg")[0],
...                requires_filters=("lut3d",), rgb_only=True)
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

#### check_params(effect, params)

Refuse parameters this registry’s schema for `effect` rejects.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### compiler(key)

The code behind a key — how a stored plan becomes runnable work.

Defaults are filled in before the code runs, so the params a plan
stores (as asked, defaults absent) are all it needs.

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis), [`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

#### cost(key)

The cost estimator, or `None` when none was declared.

* **Return type:**
  [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis), [`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`float`](https://docs.python.org/3/builtins/functions.html#float)]]]

#### declare_params(effect, schema)

Declare an effect’s parameters, once: see [`looks.params`](looks.params.html.md#module-looks.params).

The schema belongs to the registry, not to the package, so a registry
with its own implementation of an effect (a different `flatten`, say)
declares that implementation’s keys and is not bound to ours. An effect
with no declaration is not checked.

* **Raises:**
  [**RegistryError**](#looks.registry.RegistryError) – If the effect already has a different schema.
* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### effects()

Every effect with at least one implementation, sorted.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

#### has_params(effect)

Has this registry declared a schema for `effect`?

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

#### impl(key)

The declaration behind a key.

* **Raises:**
  [**UnknownImpl**](#looks.registry.UnknownImpl) – Naming what is available, because the usual cause is a
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
  * [**ImplConflict**](#looks.registry.ImplConflict) – If the key is taken.
  * [**RegistryError**](#looks.registry.RegistryError) – If the key is not `<effect>.<backend>.<variant>`,
        an ffmpeg implementation names a filter that does not exist,
        or it declares `rgb_only=False` while naming an RGB-only
        filter.
* **Return type:**
  [`ImplRef`](looks.spec.html.md#looks.spec.ImplRef)

An ffmpeg implementation’s undeclared `rgb_only` is settled here
from its `requires_filters`, so rule 22 never reads `None` for
one: leaving it out is not a way past the refusal. (Changing a
declared `rgb_only` changes `vf`’s pixels; bump `impl_version`.)

#### with_defaults(effect, params)

`params` with this registry’s declared defaults filled in.

* **Return type:**
  [`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)

### *exception* looks.registry.ImplConflict

Bases: [`RegistryError`](#looks.registry.RegistryError)

That key is taken. Last-write-wins would change what a stored plan runs.

### looks.registry.KEY_SHAPE *= '<effect>.<backend>.<variant>'*

The shape an implementation key must have, in words, for error messages.

### looks.registry.REGISTRY *= EffectRegistry(name='looks', effects=20, implementations=23)*

The registry the compiler uses when not given another.

### *exception* looks.registry.RegistryError

Bases: [`SpecError`](looks.spec.html.md#looks.spec.SpecError)

A registration that would make a later refusal point at the wrong thing.

### *exception* looks.registry.UnknownImpl

Bases: [`RegistryError`](#looks.registry.RegistryError)

A plan names an implementation this process does not have.

### looks.registry.effects()

Every effect [`REGISTRY`](#looks.registry.REGISTRY) can serve.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.registry.get_compiler(key)

The code behind a key, from [`REGISTRY`](#looks.registry.REGISTRY).

* **Return type:**
  [`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis), [`Mapping`](https://docs.python.org/3/library/typing.html#typing.Mapping)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Any`](https://docs.python.org/3/library/typing.html#typing.Any)]]

### looks.registry.get_impl(key)

The declaration behind a key, from [`REGISTRY`](#looks.registry.REGISTRY).

* **Return type:**
  [`ImplRef`](looks.spec.html.md#looks.spec.ImplRef)

### looks.registry.implementations(effect)

What [`REGISTRY`](#looks.registry.REGISTRY) has for an effect.

* **Return type:**
  [`tuple`](https://docs.python.org/3/builtins/stdtypes.html#tuple)[[`ImplRef`](looks.spec.html.md#looks.spec.ImplRef), [`...`](https://docs.python.org/3/builtins/constants.html#Ellipsis)]

### looks.registry.register_effect(impl, compiler, \*\*kwargs)

Register into [`REGISTRY`](#looks.registry.REGISTRY). See [`EffectRegistry.register()`](#looks.registry.EffectRegistry.register).

* **Return type:**
  [`ImplRef`](looks.spec.html.md#looks.spec.ImplRef)
