"""Which implementations exist, and how to reach the code behind a plan.

A :class:`~looks.spec.LookPlan` holds no live callables — that is the whole
reason it can be serialised, diffed and hashed. The consequence is that
something has to turn a stored plan back into runnable work, and a stored plan
names its implementation by **key**. This module is what those keys point at.

**A payload names a registry key and never a ``module:attr`` import path.** A
plan is a document, documents arrive from places, and a document that can name
``os:system`` is a remote-code-execution primitive wearing a schema tag. So the
only names that resolve are ones this process registered.

## A hand-rolled dict, declared as a deviation rather than discovered as one

The federation's plugin pattern is ``xdol.Registry``, and this is not it.
``xdol`` depends on ``dol``, and this package's first non-negotiable is a
``pyproject.toml`` declaring nothing but stdlib. So the *semantics* are adopted
— error on conflict, a reserved ``tags`` field — without the import. The
deviation is not novel: ``burns.RENDER_BACKENDS`` and ``muvid.visualize._VISUALS``
are both plain dicts for the same reason. A consumer that wants tag search can
mirror this mapping into an ``xdol.Registry`` in one line.

## What is refused at registration, and why there

Two things, both of which would otherwise surface much later as a confusing
*absence*:

- **A duplicate implementation key.** Last-write-wins would silently change
  which code a stored plan resolves to, which is the one failure a
  content-addressed plan hash exists to prevent.
- **An ffmpeg implementation naming a filter that does not exist.** A typo
  makes :func:`~looks.spec.select_impl` drop the candidate on a set-inclusion
  test and report "no implementation available" — a refusal whose message
  points nowhere near the cause. This is D-2's lesson applied one layer up:
  ``needs_gpl`` raises on an unrecognised filter rather than reporting it
  clean, and so does this.

A tier is **not** checked here. The registry records what exists; a
:class:`~looks.licence.Policy` refuses at selection. Registering a GPL
implementation is legitimate and necessary — refusing it at registration would
mean a caller with a GPL ceiling could not use one either.
"""

from __future__ import annotations

import functools
from typing import Any, Callable, Iterator, Mapping, Optional, Sequence

from looks.params import Param, check_params, with_defaults
from looks.spec import ImplRef, SpecError

#: What a compiler is handed and what it must return. The payload is
#: backend-shaped — see :class:`~looks.spec.Step` — and must be plain data:
#: it is about to be hashed and serialised.
Compiler = Callable[..., Mapping[str, Any]]

#: What a cost estimator returns. ``None`` means **unknown**, never free — the
#: federation's rule, and the reason this is a separate callable rather than a
#: number defaulting to 0.0.
CostFn = Callable[..., Optional[float]]

#: The shape an implementation key must have, in words, for error messages.
KEY_SHAPE = "<effect>.<backend>.<variant>"


class RegistryError(SpecError):
    """A registration that would make a later refusal point at the wrong thing."""


class ImplConflict(RegistryError):
    """That key is taken. Last-write-wins would change what a stored plan runs."""


class UnknownImpl(RegistryError):
    """A plan names an implementation this process does not have."""


class _Entry:
    """One registration: the declaration, the code, and the tags."""

    __slots__ = ("impl", "compiler", "cost", "tags")

    def __init__(
        self,
        impl: ImplRef,
        compiler: Compiler,
        cost: Optional[CostFn],
        tags: frozenset,
    ) -> None:
        self.impl = impl
        self.compiler = compiler
        self.cost = cost
        self.tags = tags


class EffectRegistry:
    """Effect name to implementations, and implementation key to code.

    An instance rather than a module global, so a test can build its own and a
    consumer can compose several. The module-level functions below delegate to
    :data:`REGISTRY`, which is the one the compiler uses by default.

    Examples:
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

        A key is taken once:

        >>> reg.register(impl, lambda params, **kw: {})
        Traceback (most recent call last):
        ...
        looks.registry.ImplConflict: 'lut3d.ffmpeg.default' is already
        registered...

        An unknown effect is an empty tuple, not an error — asking what is
        available is not the same as asking for something:

        >>> reg.implementations("nonesuch")
        ()
    """

    def __init__(self, name: str = "looks") -> None:
        self.name = name
        self._by_key: dict[str, _Entry] = {}
        self._by_effect: dict[str, list[str]] = {}
        self._params: dict[str, Mapping[str, Param]] = {}

    def register(
        self,
        impl: ImplRef,
        compiler: Compiler,
        *,
        cost: Optional[CostFn] = None,
        tags: Sequence[str] = (),
        known_filters: Optional[frozenset] = None,
    ) -> ImplRef:
        """Record an implementation. Returns it, so this reads well inline.

        Args:
            impl: What the implementation declares about itself — terms, never
                a tier.
            compiler: ``(params, *, clip, env) -> payload``. Must return plain
                data; the payload is hashed.
            cost: ``(params, *, clip, env) -> float | None`` in CPU-seconds.
                Absent means unknown, which is **not** zero.
            tags: Reserved for consumer-side search, as ``xdol.Registry`` has.
                Never read by selection — a tag that changed a refusal would be
                a tier a caller could assert.
            known_filters: The filter universe to validate against. Defaults to
                the one compiled into this package. Pass a binary's own set to
                validate against that instead.

        Raises:
            ImplConflict: If the key is taken.
            RegistryError: If the key is not ``<effect>.<backend>.<variant>``,
                an ffmpeg implementation names a filter that does not exist,
                or it declares ``rgb_only=False`` while naming an RGB-only
                filter.

        An ffmpeg implementation's undeclared ``rgb_only`` is settled here
        from its ``requires_filters``, so rule 22 never reads ``None`` for
        one: leaving it out is not a way past the refusal. (Changing a
        declared ``rgb_only`` changes ``vf``'s pixels; bump ``impl_version``.)
        """
        self._check_key(impl)
        if impl.impl in self._by_key:
            existing = self._by_key[impl.impl].impl
            raise ImplConflict(
                f"{impl.impl!r} is already registered, for effect "
                f"{existing.effect!r}. Overwriting it would silently change "
                "which code a stored plan resolves to — which is exactly what "
                "a plan hash exists to prevent. Pick another variant name."
            )
        if impl.backend == "frame":
            impl = self._settle_frame_rgb_only(impl)
        if impl.backend == "ffmpeg":
            impl = self._settle_rgb_only(impl)
            if impl.requires_filters:
                self._check_filters(impl, known_filters)
        self._by_key[impl.impl] = _Entry(impl, compiler, cost, frozenset(tags))
        self._by_effect.setdefault(impl.effect, []).append(impl.impl)
        return impl

    def declare_params(self, effect: str, schema: Mapping[str, Param]) -> None:
        """Declare an effect's parameters, once: see :mod:`looks.params`.

        The schema belongs to the registry, not to the package, so a registry
        with its own implementation of an effect (a different ``flatten``, say)
        declares that implementation's keys and is not bound to ours. An effect
        with no declaration is not checked.

        Raises:
            RegistryError: If the effect already has a different schema.
        """
        if self._params.get(effect, schema) is not schema:
            raise RegistryError(
                f"{effect!r} already has a parameter schema. A second would "
                "change what a stored Look means."
            )
        self._params[effect] = schema

    def has_params(self, effect: str) -> bool:
        """Has this registry declared a schema for ``effect``?"""
        return effect in self._params

    def check_params(self, effect: str, params: Mapping[str, Any]) -> None:
        """Refuse parameters this registry's schema for ``effect`` rejects."""
        check_params(effect, params, schemas=self._params)

    def with_defaults(self, effect: str, params: Mapping[str, Any]) -> dict:
        """``params`` with this registry's declared defaults filled in."""
        return with_defaults(effect, params, schemas=self._params)

    @staticmethod
    def _check_key(impl: ImplRef) -> None:
        parts = impl.impl.split(".")
        if len(parts) != 3:
            raise RegistryError(
                f"{impl.impl!r} is not of the form {KEY_SHAPE} — a key with "
                f"{len(parts)} segments cannot be read back into its parts."
            )
        effect, backend, _variant = parts
        if effect != impl.effect or backend != impl.backend:
            raise RegistryError(
                f"{impl.impl!r} disagrees with what it declares: effect "
                f"{impl.effect!r}, backend {impl.backend!r}. The key is "
                f"{KEY_SHAPE}, so a key that says otherwise is a name that "
                "will be read wrongly by everything downstream."
            )

    @staticmethod
    def _settle_frame_rgb_only(impl: ImplRef) -> ImplRef:
        """A frame operation always takes RGB: the pipe converts to it (rule 22).

        The conversion is ffmpeg's, at the pipe's edges, so a frame operation is
        an RGB-only step whatever it does with the pixels (issue #46).
        """
        import dataclasses

        if impl.rgb_only is False:
            raise RegistryError(
                f"{impl.impl!r} declares rgb_only=False, but a frame operation "
                "reads RGB frames off the pipe: ffmpeg converts YUV to RGB for it "
                "(rule 22). Leave it undeclared, or True."
            )
        return dataclasses.replace(impl, rgb_only=True)

    @staticmethod
    def _settle_rgb_only(impl: ImplRef) -> ImplRef:
        import dataclasses

        from looks.ffmpeg import is_rgb_domain

        derived = is_rgb_domain(impl.requires_filters)
        if impl.rgb_only is None:
            return dataclasses.replace(impl, rgb_only=derived)
        if derived and impl.rgb_only is False:
            raise RegistryError(
                f"{impl.impl!r} declares rgb_only=False but names an RGB-only "
                f"filter in {impl.requires_filters!r}: ffmpeg would convert "
                "around it with the colour tags ignored (rule 22)"
            )
        return impl

    @staticmethod
    def _check_filters(impl: ImplRef, known: Optional[frozenset]) -> None:
        from looks.environment import known_filters as _known

        universe = _known() if known is None else known
        unknown = sorted(set(impl.requires_filters) - set(universe))
        if unknown:
            raise RegistryError(
                f"{impl.impl!r} requires {unknown}, which are not ffmpeg "
                f"filters ({len(universe)} known). Left in, a typo makes "
                "selection drop this candidate on a set-inclusion test and "
                "report 'no implementation available' — a refusal pointing "
                "nowhere near the cause. Case matters to ffmpeg."
            )

    def implementations(self, effect: str) -> tuple[ImplRef, ...]:
        """Everything registered for an effect, registration order preserved."""
        return tuple(self._by_key[key].impl for key in self._by_effect.get(effect, ()))

    def effects(self) -> tuple[str, ...]:
        """Every effect with at least one implementation, sorted."""
        return tuple(sorted(self._by_effect))

    def impl(self, key: str) -> ImplRef:
        """The declaration behind a key.

        Raises:
            UnknownImpl: Naming what is available, because the usual cause is a
                plan compiled where a different set was registered.
        """
        return self._entry(key).impl

    def compiler(self, key: str) -> Compiler:
        """The code behind a key — how a stored plan becomes runnable work.

        Defaults are filled in before the code runs, so the params a plan
        stores (as asked, defaults absent) are all it needs.
        """
        entry = self._entry(key)
        return self._defaulting(entry.impl.effect, entry.compiler)

    def cost(self, key: str) -> Optional[CostFn]:
        """The cost estimator, or ``None`` when none was declared."""
        entry = self._entry(key)
        return (
            None
            if entry.cost is None
            else self._defaulting(entry.impl.effect, entry.cost)
        )

    def _defaulting(self, effect: str, function):
        @functools.wraps(function)
        def with_defaults_applied(params, **kwargs):
            # A stored plan may have been edited or come from elsewhere: the
            # compiler is a chokepoint, so it is checked here too.
            self.check_params(effect, params)
            return function(self.with_defaults(effect, params), **kwargs)

        return with_defaults_applied

    def tags(self, key: str) -> frozenset:
        return self._entry(key).tags

    def _entry(self, key: str) -> _Entry:
        try:
            return self._by_key[key]
        except KeyError:
            raise UnknownImpl(
                f"nothing is registered as {key!r}. This process has "
                f"{len(self._by_key)} implementations across "
                f"{len(self._by_effect)} effects. A plan naming an absent "
                "implementation was compiled somewhere else — which is a "
                "refusal, not a reason to guess a substitute."
            ) from None

    def __contains__(self, key: object) -> bool:
        return key in self._by_key

    def __len__(self) -> int:
        return len(self._by_key)

    def __iter__(self) -> Iterator[str]:
        return iter(self._by_key)

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(name={self.name!r}, "
            f"effects={len(self._by_effect)}, implementations={len(self._by_key)})"
        )


#: The registry the compiler uses when not given another.
REGISTRY = EffectRegistry()


def register_effect(impl: ImplRef, compiler: Compiler, **kwargs) -> ImplRef:
    """Register into :data:`REGISTRY`. See :meth:`EffectRegistry.register`."""
    return REGISTRY.register(impl, compiler, **kwargs)


def implementations(effect: str) -> tuple[ImplRef, ...]:
    """What :data:`REGISTRY` has for an effect."""
    return REGISTRY.implementations(effect)


def effects() -> tuple[str, ...]:
    """Every effect :data:`REGISTRY` can serve."""
    return REGISTRY.effects()


def get_impl(key: str) -> ImplRef:
    """The declaration behind a key, from :data:`REGISTRY`."""
    return REGISTRY.impl(key)


def get_compiler(key: str) -> Compiler:
    """The code behind a key, from :data:`REGISTRY`."""
    return REGISTRY.compiler(key)
