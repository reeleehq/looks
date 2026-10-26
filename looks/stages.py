"""The canonical stage order, and a check that warns when a Look departs from it.

The effect catalogue (``docs/research/13`` §1.3) states an order that is
load-bearing rather than aesthetic::

    geometry -> grade -> flatten -> look (LUT, posterize) -> optical -> grain

Five measured constraints sit behind it: nothing that resamples after
``posterize`` (downscale-after-posterize left 359 distinct colours where
downscale-before left 77); ``flatten`` before the LUT; ``grain`` last (before a
LUT it is colour-mapped, before ``posterize`` it is quantised away); optical
effects after the look; ``deband`` before ``posterize``.

``looks`` **validates and warns, never reorders**: the order asked for is the
order compiled, and a departure from the canon is sometimes deliberate. The
stage is a property of *what an effect does*, so it is declared here per
effect, never per implementation (the same rule that puts parameter checks in
``looks.compile`` rather than inside a compiler). An effect with no stage is
unconstrained, and the table is an argument of :func:`check_stage_order`.

Callers who want a refusal rather than a warning escalate the category:
``warnings.simplefilter("error", StageOrderWarning)``.

Examples:
    >>> from looks.spec import Effect
    >>> check_stage_order([Effect(name="grain"), Effect(name="lut3d")])
    ['lut3d (stage look) follows grain (stage grain); the canonical order is geometry -> grade -> flatten -> look -> optical -> grain']
    >>> check_stage_order([Effect(name="lut3d"), Effect(name="grain")])
    []
"""

from __future__ import annotations

import enum
from typing import Iterable, Mapping

from looks.spec import Effect


class StageOrderWarning(UserWarning):
    """A Look puts an effect in a stage the catalogue measured as wrong."""


class Stage(enum.IntEnum):
    """Pipeline stages, in canonical order."""

    GEOMETRY = 0
    GRADE = 1
    FLATTEN = 2
    LOOK = 3
    OPTICAL = 4
    GRAIN = 5


#: Effect name -> stage. An effect absent from here is unconstrained.
EFFECT_STAGES: Mapping[str, Stage] = {
    **dict.fromkeys(("fit", "fill", "stretch", "motion"), Stage.GEOMETRY),
    **dict.fromkeys(
        ("levels", "gamma", "contrast", "saturation", "curves", "colorbalance"),
        Stage.GRADE,
    ),
    "flatten": Stage.FLATTEN,
    **dict.fromkeys(("gradient_map", "lut3d", "posterize"), Stage.LOOK),
    **dict.fromkeys(("halation", "vignette"), Stage.OPTICAL),
    "grain": Stage.GRAIN,
}

#: Effects that resample, interpolate or smooth the picture, and so manufacture
#: in-between values. After `posterize` they un-quantise it. Includes the LUT
#: effects (posterise-then-LUT: 96 distinct colours against LUT-then-posterise's
#: 51, note 05) and `gate_weave`, which has no stage but still resamples.
RESAMPLING_EFFECTS = frozenset(
    {
        "fit",
        "fill",
        "stretch",
        "motion",
        "gate_weave",
        "lut3d",
        "gradient_map",
        "blur",
        "sharpen",
    }
)

#: The effect after which nothing may resample.
QUANTISER = "posterize"

_CANON = " -> ".join(s.name.lower() for s in Stage)


def check_stage_order(
    effects: Iterable[Effect],
    *,
    stages: Mapping[str, Stage] = EFFECT_STAGES,
    resampling: frozenset = RESAMPLING_EFFECTS,
    quantiser: str = QUANTISER,
) -> list[str]:
    """Describe each departure from the canonical order; empty when there is none.

    Each message names the offending (later) effect once, against the first
    earlier effect that belongs after it.

    Examples:
        >>> from looks.spec import Effect
        >>> check_stage_order([Effect(name="posterize"), Effect(name="fit")])  # doctest: +ELLIPSIS
        ['fit resamples the picture after posterize...']
        >>> check_stage_order([Effect(name="fit"), Effect(name="saturation"), Effect(name="grain")])
        []
    """
    messages = []
    seen: list[tuple[str, Stage]] = []
    quantised = False
    for effect in effects:
        name = effect.name
        if quantised and name in resampling:
            messages.append(
                f"{name} resamples the picture after {quantiser}, which "
                "un-quantises it (measured: downscaling after posterize left "
                "359 distinct colours where before it left 77; a LUT after it, "
                "96 where before it, 51)"
            )
        elif name in stages:
            stage = stages[name]
            earlier = next(((n, s) for n, s in seen if s > stage), None)
            if earlier is not None:
                messages.append(
                    f"{name} (stage {stage.name.lower()}) follows "
                    f"{earlier[0]} (stage {earlier[1].name.lower()}); "
                    f"the canonical order is {_CANON}"
                )
        if name in stages:
            seen.append((name, stages[name]))
        quantised = quantised or name == quantiser
    return messages
