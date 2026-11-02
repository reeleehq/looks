"""How one shot gives way to the next — the vocabulary, not the graph.

ffmpeg's ``xfade`` offers 58 transitions on this build. This package carries
**sixteen**, and the reason is the posture rather than the number: a name a
caller passes should be refused here, at the boundary, rather than discovered
three stages later as an ffmpeg error. Measured — an unrecognised curve produces

    [Parsed_xfade_0] const_values array too small for transition
    Error applying option 'transition' to filter 'xfade':
        Not yet implemented in FFmpeg, patches welcome

which names neither the caller's mistake nor the filter's actual complaint. A
vocabulary we own is a vocabulary we can keep working across ffmpeg builds, and
translating at the boundary is the same rule `muvid`'s EDL and `an`'s camera
table already follow.

## Why this module emits no filter

Every other compiler here returns a string. This one returns **options**, because
``xfade`` takes *two* video inputs and a compiled fragment in this package
references no input index at all — that is rule 20, and it is what lets a
fragment splice into a bare ``-vf``, into a per-cut chain, and into a pipe's
encoder half alike. A two-input filter cannot satisfy it.

So `looks` owns the curve names, the record, and the floor; the host owns the
filtergraph that wires two streams into an ``xfade``. That is the same split as
everywhere else: this package decides *what*, the caller decides *where*.

## A short transition is a hard cut wearing a label, and the floor is not a constant

Measured counting frames that are neither source colour. The numbers below
were taken on ffmpeg 8.1 and re-verified unchanged on **6.1.6 and 9.0.1**,
which is why they are stated as a property of the filter rather than of a
build — `speed=0` and a height-1 frame both looked like properties of ffmpeg
until CI ran a different one:

=========  ==========  ===============
fps        duration    blended frames
=========  ==========  ===============
30         0.30 s      8
30         0.10 s      2
30         0.04 s      1
30         0.033 s     **0**
10         0.30 s      2
10         0.10 s      **0**
=========  ==========  ===============

So a transition shorter than about one frame period produces **no blended frame
at all** — the picture cuts, and the record says it faded. ``duration=0`` is
accepted by ffmpeg without complaint.

:data:`MIN_TRANSITION_S` is inherited from `muvid` at 0.04 s, which is exactly
one frame at 25 fps — which is where the number came from, and why it is *too
small* at lower rates. :func:`blended_frames` is the honest form: it takes the
rate, because the question does.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Optional

from looks.params import (
    DFLT_RIPPLE_AMPLITUDE,
    DFLT_RIPPLE_BLOOM,
    DFLT_RIPPLE_WAVELENGTHS,
    ParamError,
    check_params,
)
from looks.spec import Effect, SpecError

#: The transitions this package offers: a curated subset of ffmpeg's 58, chosen
#: because they read as deliberate edits rather than as effects. Adding one is a
#: decision — the point of an owned vocabulary is that it does not grow by
#: accident — and every name here is verified present in ffmpeg's ``xfade``.
TRANSITION_CURVES = frozenset(
    {
        "fade",
        "fadeblack",
        "fadewhite",
        "dissolve",
        "wipeleft",
        "wiperight",
        "wipeup",
        "wipedown",
        "slideleft",
        "slideright",
        "slideup",
        "slidedown",
        "smoothleft",
        "smoothright",
        "circleopen",
        "circleclose",
    }
)

#: The default curve. A plain cross-fade, because it is the one that reads as
#: no decision at all.
DFLT_CURVE = "fade"

#: The floor below which a transition is a hard cut wearing a label. Inherited
#: from `muvid`, where it is 0.04 s — **exactly one frame at 25 fps**, which is
#: where the number comes from. It is therefore too small at lower rates, and
#: :func:`blended_frames` is the form that knows it: prefer that when the rate
#: is available, and treat this as the rate-free fallback it is.
MIN_TRANSITION_S = 0.04


#: The ``kind`` a :class:`Transition` document may carry. :meth:`Transition.
#: to_dict` writes none, so a document without one is an ``xfade`` transition;
#: any other kind is refused rather than read as a fade.
XFADE_KIND = "xfade"
#: The ``kind`` a :class:`Ripple` document carries, and must.
RIPPLE_KIND = "ripple"


class TransitionError(SpecError):
    """A transition that cannot be honoured as asked."""


@dataclass(frozen=True)
class Transition:
    """How a shot blends in from its predecessor.

    A record rather than a bare float, so the curve — and anything after it — is
    an additive field rather than another shape change on something already
    serialised.

    The transition belongs to the shot it is *on*: it annotates that shot's
    **entrance**. `muvid`'s EDL keeps it that way so spans stay one per span, and
    the reasoning for that invariant stays there — this is the vocabulary, not
    the edit model.

    Examples:
        >>> Transition(0.5)
        Transition(duration_s=0.5, curve='fade')
        >>> Transition(0.5, 'circleopen').curve
        'circleopen'

        A name outside the vocabulary is refused here, not by ffmpeg later:

        >>> Transition(0.5, 'starwipe')
        Traceback (most recent call last):
        ...
        looks.transition.TransitionError: 'starwipe' is not a transition this
        package offers...

        And a duration that cannot be a transition:

        >>> Transition(0.0)
        Traceback (most recent call last):
        ...
        looks.transition.TransitionError: a transition needs a positive
        duration; got 0.0...
    """

    duration_s: float
    curve: str = DFLT_CURVE

    def __post_init__(self) -> None:
        if not (self.duration_s > 0):
            raise TransitionError(
                f"a transition needs a positive duration; got "
                f"{self.duration_s!r}. ffmpeg accepts duration=0 without "
                "complaint and cuts, so a zero here would be a fade in the "
                "record and a cut on screen."
            )
        if self.curve not in TRANSITION_CURVES:
            near = sorted(c for c in TRANSITION_CURVES if c[:4] == self.curve[:4])
            raise TransitionError(
                f"{self.curve!r} is not a transition this package offers. "
                f"Available: {sorted(TRANSITION_CURVES)}."
                + (f" Did you mean {near}?" if near else "")
                + " ffmpeg's own refusal for an unknown name is 'Not yet "
                "implemented in FFmpeg, patches welcome', which names neither "
                "the mistake nor the filter — which is why this is refused here."
            )

    def to_dict(self) -> dict:
        return {"duration_s": self.duration_s, "curve": self.curve}

    @classmethod
    def from_dict(cls, d: Mapping) -> "Transition":
        kind = d.get("kind", XFADE_KIND)
        if kind != XFADE_KIND:
            raise TransitionError(
                f"not a Transition document: its kind is {kind!r}. A "
                f"{RIPPLE_KIND!r} document is read with Ripple.from_dict; read "
                "as a Transition it would silently become a plain fade."
            )
        return cls(
            duration_s=float(d["duration_s"]),
            curve=str(d.get("curve", DFLT_CURVE)),
        )


@dataclass(frozen=True)
class Ripple:
    """A dream transition: the picture ripples, blooms and dissolves into the next.

    Not a :data:`TRANSITION_CURVES` name, because ``xfade`` cannot move a
    pixel. It is two things the host already knows how to place, over one
    window:

    * :attr:`dissolve`, an ordinary :class:`Transition` for the host's
      ``xfade``, as for any other transition. It is ``xfade``'s linear
      ``fade``; the production this came from (issue #49) used a smoothstep
      blend, which no :data:`TRANSITION_CURVES` name gives.
    * :meth:`effect`, a single-input ``ripple`` effect, swelling from nothing
      at the window's start to its peak at the middle of the fade and settling
      by its end. It compiles through :func:`looks.compile_look` like any
      effect, so it carries a licence tier.

    **Where the effect goes.** On the stream that holds *both* shots across the
    window, the composite the dissolve produces, with ``offset`` the dissolve's
    start in *that stream's own timeline*, after any ``setpts`` the host
    applies. The trap: a host that runs ``xfade`` at offset 0 and then shifts
    the result into place with ``setpts`` (as ``reeleehq/mixing``'s
    ``_entrance`` does) must pass the shifted start ``t0``, or apply the
    effect *before* the shift with ``offset=0``. Pass the unshifted 0 after
    the shift and the ripple runs on the wrong frames, with no error.

    **What it cannot do.** A window of about one frame period or less blends
    nothing and ripples on at most one frame: call
    :func:`check_visible` on :attr:`dissolve` with the rate. The bloom's blur
    is sized from :attr:`ClipSpec.height <looks.spec.ClipSpec>` at compile
    time, while the warp scales with the frame at run time, so compile against
    the clip the effect will actually run on. The motion's phases are counted
    from the window's start, so the same record is the same picture wherever
    the window lands.

    Sizes are fractions of the frame (``amplitude`` of its width,
    ``wavelengths`` of its height), so a look reads the same at any resolution;
    the defaults are 18 px and 86/33 px at 1024x576, judged on real footage.

    Examples:
        >>> r = Ripple(1.0)
        >>> r.dissolve
        Transition(duration_s=1.0, curve='fade')
        >>> e = r.effect(offset=6.3)
        >>> e.name, e.params["start_s"], e.params["duration_s"]
        ('ripple', 6.3, 1.0)
        >>> r.to_dict()["kind"]
        'ripple'
        >>> Ripple.from_dict(r.to_dict()) == r
        True
        >>> Ripple(1.0, bloom=2)
        Traceback (most recent call last):
        ...
        looks.transition.TransitionError: ripple: bloom must be a number in [0, 1]; got 2

        A stored cross-fade is not read as a ripple, nor a ripple as a fade:

        >>> Ripple.from_dict({"duration_s": 1.0, "curve": "fade"})
        Traceback (most recent call last):
        ...
        looks.transition.TransitionError: not a Ripple document...
        >>> Transition.from_dict(r.to_dict())
        Traceback (most recent call last):
        ...
        looks.transition.TransitionError: not a Transition document...
    """

    duration_s: float
    amplitude: float = DFLT_RIPPLE_AMPLITUDE
    wavelengths: tuple[float, float] = DFLT_RIPPLE_WAVELENGTHS
    bloom: float = DFLT_RIPPLE_BLOOM

    def __post_init__(self) -> None:
        object.__setattr__(self, "wavelengths", tuple(self.wavelengths))
        # A non-positive duration is refused by Transition, word for word.
        Transition(self.duration_s)
        try:
            check_params("ripple", self.effect(offset=0).params)
        except ParamError as error:
            raise TransitionError(str(error)) from error

    @property
    def dissolve(self) -> Transition:
        """The cross-fade the host runs between the two shots."""
        return Transition(self.duration_s, DFLT_CURVE)

    def effect(self, *, offset: float) -> Effect:
        """The warp, for the stream that holds both shots across the window.

        ``offset`` is the dissolve's start in *that* stream's own timeline: the
        number passed to ``xfade`` (:func:`xfade_options`) when the effect runs
        on ``xfade``'s output directly, or the shifted start when the host
        moves that output with ``setpts`` first (see the class docstring). The
        warp's peak then lands on the fade's midpoint.
        """
        return Effect(
            name="ripple",
            params={
                "start_s": offset,
                "duration_s": self.duration_s,
                "amplitude": self.amplitude,
                "wavelengths": self.wavelengths,
                "bloom": self.bloom,
            },
        )

    def to_dict(self) -> dict:
        return {
            "kind": RIPPLE_KIND,
            "duration_s": self.duration_s,
            "amplitude": self.amplitude,
            "wavelengths": self.wavelengths,
            "bloom": self.bloom,
        }

    @classmethod
    def from_dict(cls, d: Mapping) -> "Ripple":
        if d.get("kind") != RIPPLE_KIND:
            raise TransitionError(
                f"not a Ripple document: its kind is {d.get('kind')!r}, not "
                f"{RIPPLE_KIND!r}. A Transition document has no kind; read it "
                "with Transition.from_dict."
            )
        return cls(
            duration_s=float(d["duration_s"]),
            amplitude=float(d.get("amplitude", DFLT_RIPPLE_AMPLITUDE)),
            wavelengths=tuple(
                float(w) for w in d.get("wavelengths", DFLT_RIPPLE_WAVELENGTHS)
            ),
            bloom=float(d.get("bloom", DFLT_RIPPLE_BLOOM)),
        )


def blended_frames(
    transition: Transition, fps: float, *, offset: Optional[float] = None
) -> int:
    """How many frames will be a mixture of the two shots.

    **This is a GUARANTEED MINIMUM unless you pass ``offset``**, and that is not
    a hedge — the count genuinely depends on where the transition starts. A
    frame blends when its time ``k/fps`` falls strictly inside
    ``(offset, offset + duration)``; an open interval of length ``D`` contains at
    least ``ceil(D) - 1`` integers and at most ``floor(D)``, and which one you
    get is decided by the offset's fractional position. Measured against ffmpeg:
    0.10 s at 30 fps blends **2** frames at ``offset=0.5`` and **3** at
    ``offset=0.42``.

    An earlier version returned ``floor(D) - 1`` and described it as the count.
    That is below the true minimum whenever ``D`` is not an integer, so it
    under-reported — the safe direction for :func:`is_hard_cut`, but it
    contradicted this module's own measured table (0.04 s at 30 fps blends 1
    frame; the formula said 0) and the tests never noticed because every row in
    the parametrisation sat where the two formulas happen to agree.

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
    """
    if fps <= 0:
        raise TransitionError(f"fps must be positive; got {fps!r}")
    span = transition.duration_s * fps
    if offset is None:
        # The minimum over every offset: what a caller who does not know where
        # the transition lands can rely on.
        return max(0, int(math.ceil(span)) - 1)
    if offset < 0:
        raise TransitionError(f"offset must not be negative; got {offset!r}")
    lo, hi = offset * fps, (offset + transition.duration_s) * fps
    return max(0, _integers_strictly_between(lo, hi))


def _integers_strictly_between(lo: float, hi: float) -> int:
    """How many integers ``k`` satisfy ``lo < k < hi``.

    Frame times are ``k/fps``; a frame at exactly the transition's start or end
    carries a pure source, so the interval is open at both ends. Exactness at
    the boundary is the whole difficulty, which is why this is separate and
    tested directly rather than inlined into an expression.
    """
    first = int(math.floor(lo)) + 1
    last = int(math.ceil(hi)) - 1
    return max(0, last - first + 1)


def max_blended_frames(transition: Transition, fps: float) -> int:
    """The most frames this transition can blend, over every offset.

    The companion to :func:`blended_frames`' minimum. The pair is what makes the
    uncertainty legible instead of hiding it inside a single number that is
    right for one offset.

    An open interval of length ``D`` contains at most ``ceil(D)`` integers —
    NOT ``floor(D)``, which is what intuition offers and what the first draft of
    this function returned. A 0.04 s transition at 10 fps spans 0.4 of a frame
    period and still blends one frame when it straddles a frame time
    (``offset=0.17`` puts the window at (1.7, 2.1), which contains 2). The
    bracket test caught it.

    >>> blended_frames(Transition(0.25), 30), max_blended_frames(Transition(0.25), 30)
    (7, 8)
    >>> blended_frames(Transition(0.04), 10), max_blended_frames(Transition(0.04), 10)
    (0, 1)
    """
    if fps <= 0:
        raise TransitionError(f"fps must be positive; got {fps!r}")
    return max(0, int(math.ceil(transition.duration_s * fps)))


def is_hard_cut(
    transition: Transition, fps: float, *, offset: Optional[float] = None
) -> bool:
    """Will this transition produce no blended frame at all?

    Without ``offset`` this is "might it blend nothing, at some offset" — the
    conservative reading, since :func:`blended_frames` returns the minimum.
    With one it is the exact answer for that placement.

    >>> is_hard_cut(Transition(0.30), 30)
    False
    >>> is_hard_cut(Transition(0.10), 10)
    True
    """
    return blended_frames(transition, fps, offset=offset) == 0


def check_visible(
    transition: Transition, fps: float, *, offset: Optional[float] = None
) -> None:
    """Raise unless the transition will actually be seen.

    Call it when the rate is known. A transition that blends nothing is not a
    subtle transition — it is a cut, and a record saying otherwise is the kind
    of quiet disagreement between plan and picture this package exists to
    prevent.

    >>> check_visible(Transition(0.30), 30)
    >>> check_visible(Transition(0.05), 10)
    Traceback (most recent call last):
    ...
    looks.transition.TransitionError: a 0.05 s transition at 10 fps blends 0
    frames...
    """
    if is_hard_cut(transition, fps, offset=offset):
        # A transition is guaranteed visible once its span exceeds ONE frame
        # period: an open interval of length D contains at least ceil(D) - 1
        # frame times, so D > 1 is the threshold. This used to advise 2/fps,
        # which overstates the requirement by up to 2x and would have a caller
        # lengthen a transition that was already fine.
        needed = 1.0 / fps
        raise TransitionError(
            f"a {transition.duration_s:g} s transition at {fps:g} fps blends 0 "
            f"frames — it is a hard cut, and calling it {transition.curve!r} in "
            f"the record would be the only place the fade exists. It needs to "
            f"be longer than {needed:.3g} s at this rate (one frame period); "
            f"anything shorter blends nothing at some offsets and one frame at "
            f"others."
        )


def xfade_options(
    transition: Transition,
    *,
    offset: float,
    fps: Optional[float] = None,
    first_clip_s: Optional[float] = None,
) -> dict:
    """The ``xfade`` options for this transition — options, not a filter.

    ``xfade`` takes two video inputs, and a compiled fragment in this package
    references no input index (rule 20). So the host wires the two streams and
    splices these options in; `looks` says what the transition IS.

    Args:
        offset: When the transition starts, in the output's timeline. The host's
            number, because it depends on how the host laid out its cuts.
        fps: When given, the transition is checked against it — a transition
            that blends nothing is refused rather than emitted.
        first_clip_s: The duration of the stream the transition starts in. When
            given, an offset the clip cannot reach is refused. ffmpeg does NOT
            refuse it: measured on two 1.0 s clips, ``offset=1.5`` exits 0 and
            blends nothing — a fade in the record and a cut on screen, which is
            the same failure a zero duration is refused for.

    Examples:
        >>> xfade_options(Transition(0.5, 'circleopen'), offset=2.0)
        {'transition': 'circleopen', 'duration': 0.5, 'offset': 2.0}

        >>> xfade_options(Transition(0.02), offset=1.0, fps=25)
        Traceback (most recent call last):
        ...
        looks.transition.TransitionError: a 0.02 s transition at 25 fps blends 0
        frames...
    """
    if fps is not None:
        check_visible(transition, fps, offset=offset)
    if first_clip_s is not None and offset + transition.duration_s > first_clip_s:
        raise TransitionError(
            f"a {transition.duration_s:g} s transition at offset={offset:g} "
            f"runs to {offset + transition.duration_s:g} s, past the end of a "
            f"{first_clip_s:g} s clip. ffmpeg accepts this and exits 0 having "
            "blended nothing, so the fade would exist only in the record."
        )
    if offset < 0:
        raise TransitionError(
            f"a transition cannot start before the output does; got offset={offset!r}"
        )
    return {
        "transition": transition.curve,
        "duration": transition.duration_s,
        "offset": offset,
    }
