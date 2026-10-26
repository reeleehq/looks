"""One parameter schema per effect: names, types, defaults and bounds, once.

An effect's parameters used to live in three places that could drift: the
compiler lambdas (a default read with ``params.get(name, DFLT)``), the
effect-level checks in ``looks.compile`` (ranges), and the research catalogue.
Unknown keys were ignored, so ``colorbalance`` with ``shadow=`` (singular)
compiled to an identity grade without a word.

:data:`EFFECT_PARAMS` is the single declaration. It is read by
:func:`check_params` (``looks.compile`` calls it before an implementation is
chosen, so every implementation of an effect accepts the same documents) and by
:func:`with_defaults` (``looks.compile`` fills defaults before a compiler or
cost estimator runs, so the compilers read ``p["sigma"]``, never a second copy
of the default). Keyed by EFFECT, never by implementation: two implementations
of one effect must not disagree on what an omitted parameter means (rule 29b),
and a check inside one compiler is a check the licence tier can switch off.

An effect with no entry here is unchecked: a caller's own registered effects
are theirs to validate. A parameter declared without a default stays absent
when omitted, and the compiler decides (usually by refusing).

The checks refuse what ffmpeg would silently change or what is not a number:
``True`` and ``"0.5"`` are not floats, ``inf`` and ``nan`` are not finite,
``7.9`` is not a whole number (it would be emitted as ``7``).

Examples:
    >>> check_params("grain", {"strength": 7})
    >>> check_params("grain", {"strenght": 7})
    Traceback (most recent call last):
    ...
    looks.params.ParamError: grain: unknown parameter 'strenght'; it takes ['seed', 'strength']
    >>> with_defaults("grain", {"seed": 3})["strength"]
    8
"""

from __future__ import annotations

import math
import numbers
from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Sequence

#: A parameter with no default is left absent when omitted.
NO_DEFAULT = object()


class ParamError(ValueError):
    """Parameters no implementation of an effect could honour."""


@dataclass(frozen=True)
class Param:
    """One named parameter: how to recognise a valid value, and what omitted means.

    ``accepts`` is the strategy; the constructors below (:func:`real`,
    :func:`whole`, :func:`flag`, :func:`text`, :func:`vector`, :func:`curve`,
    :func:`anything`) cover every kind the registered effects need.
    """

    name: str
    accepts: Callable[[Any], bool]
    expects: str
    default: Any = NO_DEFAULT
    #: What sort of value this is, so a caller (or a test) can select
    #: parameters by it rather than by parsing ``expects``.
    kind: str = "any"
    #: Is the value of the right TYPE, bounds aside? A wrong type is reported
    #: as one, never as a bound it did not fail.
    is_type: Callable[[Any], bool] = lambda value: True
    type_expects: str = ""


def as_emitted(value: float) -> float:
    """A number as the compilers write it into a filter string, read back.

    A parameter check compares this, not the value asked for: six decimals are
    kept, so two curve x-points ``1e-7`` apart are written as one point, which
    ``curves`` refuses, and a vignette ``angle`` of ``1e-9`` is written ``0``.

    >>> as_emitted(1e-9)
    0.0
    >>> as_emitted(0.1234567)
    0.123457
    """
    return float(f"{float(value):.6f}")


def _is_real(value) -> bool:
    """A finite number. Not ``True``, not ``"0.5"``, not ``inf`` or ``nan``."""
    return (
        isinstance(value, numbers.Real)
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _is_whole(value) -> bool:
    """A number ffmpeg can take as an integer option without it being changed.

    ``8.0`` is accepted, deliberately: it is emitted as ``8``, the picture asked
    for. ``7.9`` (emitted ``7``), ``True`` (emitted ``1``) and ``"8"`` are not.
    """
    return _is_real(value) and (
        isinstance(value, numbers.Integral) or float(value).is_integer()
    )


def _is_sequence(value, length: Optional[int] = None) -> bool:
    """A tuple-like value. A string is a sequence too, and ``"12"`` is not ``(1, 2)``."""
    return (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes))
        and (length is None or len(value) == length)
    )


def _bounds(low, high, *, low_open=False, emitted=False):
    """A predicate for ``low <= v <= high`` (``low < v`` when ``low_open``)."""

    def within(value) -> bool:
        v = as_emitted(value) if emitted else value
        if low is not None and (v <= low if low_open else v < low):
            return False
        return high is None or v <= high

    return within


def _describe(low, high, *, low_open=False, emitted=False) -> str:
    left = "(" if low_open else "["
    suffix = ", as written to six decimals" if emitted else ""
    return f"in {left}{'-inf' if low is None else low}, {'inf' if high is None else high}]{suffix}"


def real(
    name, default=NO_DEFAULT, *, low=None, high=None, low_open=False, emitted=False
):
    """A finite number, optionally bounded. ``emitted`` bounds it as written."""
    within = _bounds(low, high, low_open=low_open, emitted=emitted)
    expects = (
        "must not be negative"
        if (low, high, low_open) == (0, None, False)
        else "must be a number "
        + _describe(low, high, low_open=low_open, emitted=emitted)
    )
    return Param(
        name,
        lambda v: _is_real(v) and within(v),
        expects,
        default,
        kind="real",
        is_type=_is_real,
        type_expects="a finite number",
    )


def whole(name, default=NO_DEFAULT, *, low=None, high=None):
    """A whole number (``8.0`` is fine, ``7.9`` and ``True`` are not)."""
    within = _bounds(low, high)
    return Param(
        name,
        lambda v: _is_whole(v) and within(v),
        "must be a whole number " + _describe(low, high),
        default,
        kind="whole",
        is_type=_is_whole,
        type_expects="a whole number",
    )


def flag(name, default=NO_DEFAULT):
    """A bool, not truthiness: ``"false"`` would otherwise be true."""
    return Param(
        name,
        lambda v: isinstance(v, bool),
        "must be True or False",
        default,
        kind="flag",
    )


def text(name, default=NO_DEFAULT):
    return Param(
        name, lambda v: isinstance(v, str), "must be a string", default, kind="text"
    )


def choice(name, options: Sequence[str], default=NO_DEFAULT):
    """One of a closed set of strings (an ffmpeg option's enum)."""
    return Param(
        name,
        lambda v: isinstance(v, str) and v in options,
        f"must be one of {list(options)}",
        default,
        kind="choice",
    )


def anything(name, default=NO_DEFAULT):
    """A key the effect takes whose shape its compiler owns (a path, a size, a ramp)."""
    return Param(name, lambda v: True, "", default)


def vector(name, length, default=NO_DEFAULT, *, low=None, high=None):
    """``length`` finite numbers, each optionally bounded."""
    within = _bounds(low, high)
    return Param(
        name,
        lambda v: _is_sequence(v, length) and all(_is_real(c) and within(c) for c in v),
        f"must be {length} numbers, each " + _describe(low, high),
        default,
        kind="vector",
        is_type=lambda v: _is_sequence(v, length) and all(_is_real(c) for c in v),
        type_expects=f"{length} finite numbers",
    )


def curve(name):
    """At least two ``(x, y)`` points in 0..1 with x strictly increasing.

    Checked as emitted: x-points closer than the six decimals the compiler
    writes become one point, and ``curves`` refuses the curve. An empty value
    is accepted, because the compiler skips an empty channel too.
    """

    def accepts(points) -> bool:
        if not points:
            return True
        if not (_is_sequence(points) and len(points) >= 2):
            return False
        if not all(_is_sequence(p, 2) and all(_is_real(c) for c in p) for p in points):
            return False
        emitted = [tuple(as_emitted(c) for c in p) for p in points]
        xs = [x for x, _y in emitted]
        return all(0 <= c <= 1 for p in emitted for c in p) and all(
            a < b for a, b in zip(xs, xs[1:])
        )

    return Param(
        name,
        accepts,
        "must be at least two (x, y) points in 0..1 with x strictly "
        "increasing at six decimals",
        kind="curve",
    )


# ----------------------------------------------------------------- defaults
# Named, with the reason each value is what it is. Defaults are the effect
# catalogue's (docs/research/13 §3) unless noted; the halation tint and the gate
# weave are the 2026-10-16 production's (issue #25).

#: Vignette half-angle, radians.
DFLT_VIGNETTE_ANGLE = math.pi / 5
#: ``vignette`` clips its angle to [0, PI/2] instead of refusing, so a larger
#: one would compile to a picture nobody asked for.
MAX_VIGNETTE_ANGLE = math.pi / 2

DFLT_HALATION_THRESHOLD = 0.78
DFLT_HALATION_SIGMA = 24.0
#: ``gblur`` refuses a larger sigma ("Result too large"; 9.0 and 6.1).
MAX_BLUR_SIGMA = 1024
DFLT_HALATION_AMOUNT = 0.5
#: Red-orange: film halation is the red layer scattering back off the base.
DFLT_HALATION_TINT = (1.0, 0.35, 0.2)

DFLT_GRAIN_STRENGTH = 8
#: ``noise``'s ``alls`` range is 0..100.
MAX_GRAIN_STRENGTH = 100
#: Pinned rather than ffmpeg's own default, for portability across builds.
#: Note ``0`` is a different picture from an unseeded ``noise``.
DFLT_GRAIN_SEED = 0
#: ``noise``'s ``all_seed`` tops out at INT_MAX; its ``-1`` (a random seed) is
#: below the range on purpose, since a seed is what makes grain reproducible.
MAX_GRAIN_SEED = 2**31 - 1

#: Gate-weave wander, in pixels either side of centre.
DFLT_WEAVE_AMPLITUDE = 2
#: Horizontal and vertical wander, Hz. Incommensurate so the path never loops
#: visibly: the production's ``n*0.9`` and ``n*0.61`` rad/frame, at 24 fps.
DFLT_WEAVE_FREQUENCY = (3.44, 2.33)

#: ``lut3d``'s interpolation. ``posterize`` after it needs ``nearest``; that is
#: the caller's choice, so the default is the filter's own.
DFLT_INTERP = "tetrahedral"

#: ``lut3d``'s ``interp`` values.
INTERP_MODES = ("nearest", "trilinear", "tetrahedral", "pyramid", "prism")

#: One code value per level on an 8-bit channel; more levels than that is the
#: identity, and an absurd count only makes a huge expression.
MAX_POSTERIZE_LEVELS = 256

#: ``bilateral``'s ranges: sigmaS 0..512, sigmaR 0..1, planes a 4-bit mask.
MAX_FLATTEN_SPATIAL = 512
MAX_FLATTEN_PLANES = 15

#: `looks` channel names to ffmpeg `curves` option names.
CURVES_CHANNELS = ("all", "red", "green", "blue")

#: `colorbalance` tonal zones, keyed to the letter its options end in.
COLORBALANCE_ZONES = {"shadows": "s", "midtones": "m", "highlights": "h"}


def _params(*params: Param) -> Mapping[str, Param]:
    return {p.name: p for p in params}


#: Effect -> its parameters. Geometry's ``target``, ``gradient_map``'s ``size``
#: and ``title``, and ``motion``'s keyframes have their defaults (or refusals)
#: where the value is built: ``looks.geometry``, ``looks.lut``, ``looks.motion``.
EFFECT_PARAMS: Mapping[str, Mapping[str, Param]] = {
    **dict.fromkeys(("fit", "fill", "stretch"), _params(anything("target"))),
    "motion": _params(
        anything("keyframes"),
        anything("output"),
        real("fps", low=0, low_open=True),
    ),
    "levels": _params(
        real("black", 0, low=-1, high=1), real("white", 1, low=-1, high=1)
    ),
    "gamma": _params(real("gamma", 1.0, low=0, low_open=True)),
    # Negative would invert the picture, which is a different effect.
    "contrast": _params(real("amount", 1.0, low=0)),
    "saturation": _params(real("amount", 1.0)),
    "curves": _params(*(curve(channel) for channel in CURVES_CHANNELS)),
    "colorbalance": _params(
        *(vector(zone, 3, (0, 0, 0), low=-1, high=1) for zone in COLORBALANCE_ZONES),
        flag("preserve_lightness", False),
    ),
    "gradient_map": _params(
        anything("stops"),
        whole("size", low=2),
        text("title"),
        real("contrast", 1.0),
        real("lift", 0.0),
        choice("interp", INTERP_MODES, DFLT_INTERP),
    ),
    "lut3d": _params(anything("cube"), choice("interp", INTERP_MODES, DFLT_INTERP)),
    "posterize": _params(whole("levels", 8, low=2, high=MAX_POSTERIZE_LEVELS)),
    "flatten": _params(
        real("spatial", 60, low=0, high=MAX_FLATTEN_SPATIAL),
        real("range", 0.05, low=0, high=1),
        # All three planes. bilateral's default is 1 — luma only — which
        # smooths the detail and leaves behind the chroma noise the flatten
        # was for.
        whole("planes", 7, low=0, high=MAX_FLATTEN_PLANES),
    ),
    # One parameter for the effect: `gblur` takes it as its sigma and `boxblur`
    # derives the radius with the same spread, so the licence tier that picks
    # the implementation does not pick the picture (rule 29b).
    "blur": _params(real("sigma", 2, low=0, high=MAX_BLUR_SIGMA)),
    # unsharp's luma_amount range.
    "sharpen": _params(real("amount", 1.0, low=-2, high=5)),
    "vignette": _params(
        real(
            "angle",
            DFLT_VIGNETTE_ANGLE,
            low=0,
            high=MAX_VIGNETTE_ANGLE,
            low_open=True,
            emitted=True,
        )
    ),
    "halation": _params(
        real("threshold", DFLT_HALATION_THRESHOLD, low=0, high=1),
        real(
            "sigma",
            DFLT_HALATION_SIGMA,
            low=0,
            high=MAX_BLUR_SIGMA,
            low_open=True,
            emitted=True,
        ),
        real("amount", DFLT_HALATION_AMOUNT, low=0, high=1),
        vector("tint", 3, DFLT_HALATION_TINT, low=0),
    ),
    "grain": _params(
        whole("strength", DFLT_GRAIN_STRENGTH, low=0, high=MAX_GRAIN_STRENGTH),
        whole("seed", DFLT_GRAIN_SEED, low=0, high=MAX_GRAIN_SEED),
    ),
    "gate_weave": _params(
        whole("amplitude", DFLT_WEAVE_AMPLITUDE, low=0),
        vector("frequency", 2, DFLT_WEAVE_FREQUENCY, low=0),
    ),
}

#: A refused key that deserves more than "unknown parameter".
PARAM_HINTS: Mapping[tuple[str, str], str] = {
    ("grain", "temporal"): (
        "there is no 'temporal' switch: grain is always re-drawn per frame, "
        "because static noise reads as dirt on the lens, not as grain"
    ),
}


def check_params(
    effect: str,
    params: Mapping[str, Any],
    *,
    schemas: Mapping[str, Mapping[str, Param]] = EFFECT_PARAMS,
) -> None:
    """Refuse an unknown key or a value the effect could not honour.

    An effect with no schema is not checked. Only present keys are checked:
    an absent one takes its declared default, so a check never has a second
    copy of it.

    Raises:
        ParamError: Naming the effect, the key and what it expects.
    """
    schema = schemas.get(effect)
    if schema is None:
        return
    for key, value in params.items():
        if key not in schema:
            hint = PARAM_HINTS.get((effect, key))
            raise ParamError(
                f"{effect}: {hint}"
                if hint
                else f"{effect}: unknown parameter {key!r}; it takes {sorted(schema)}"
            )
        param = schema[key]
        if not param.is_type(value):
            raise ParamError(
                f"{effect}: {key} must be {param.type_expects}; got {value!r}"
            )
        if not param.accepts(value):
            raise ParamError(f"{effect}: {key} {param.expects}; got {value!r}")


def with_defaults(
    effect: str,
    params: Mapping[str, Any],
    *,
    schemas: Mapping[str, Mapping[str, Param]] = EFFECT_PARAMS,
) -> dict:
    """The parameters with every declared default filled in; the input is untouched."""
    defaults = {
        p.name: p.default
        for p in schemas.get(effect, {}).values()
        if p.default is not NO_DEFAULT
    }
    return {**defaults, **params}
