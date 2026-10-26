"""The ffmpeg backend: filter strings, escaping, and the first effects.

This is where a `Step`'s payload becomes text another process will parse, which
is the whole reason the escaping in here is not a detail. Everything else in the
package produces data; this module produces a *string handed to a parser*, and
the flagship effect takes a caller-supplied file path.

## Escaping, and why once is not enough

ffmpeg unescapes a filter option **twice**. The filtergraph parser reads the
whole graph first, splitting on ``,`` ``;`` ``[`` ``]`` and consuming one layer
of quoting; only then is each surviving per-filter argument split into options
on ``:``, consuming a second. So escaping runs in the **mirror order** — option
level first, graph level over that result — and each ffmpeg pass peels off
exactly one layer.

Ported from ``muvid.visualize.canvas.escape_filter_value``, with its recorded
negative kept: **``%`` is deliberately not escaped.** Neither parser treats it
as special, so ``\\%`` was simply unescaped back to ``%`` and escaping it never
did anything. ``drawtext``'s ``%{...}`` expansion is a third level belonging to
one filter's ``text`` option, and is out of scope for a general escaper.

Verified here rather than inherited: ``-vf "lut3d=file=id,with:comma.cube"``
fails, and the escaped form works.

## LGPL first, and the alternate says why

Where an effect has both a GPL-gated and an LGPL implementation, **both are
registered** and the LGPL one carries the lower ``preference``. That is not a
licence judgement made here — the registry records what exists and a
:class:`~looks.licence.Policy` refuses at selection — it is an ordering, so that
a caller who never thinks about licences gets the portable answer by default and
a caller who needs the GPL one can still pin it.

``eq`` is the case worth naming: the obvious grade filter is GPL-only, three of
its jobs have LGPL substitutes in the same binary, and `muvid` ships a single
``eq=`` for a cosmetic dim. That one filter call is the concrete argument for
this package existing.

## What is deliberately absent

No encoder arguments, no output file, no process. A payload here is a filter
fragment and nothing more — the moment this module grows an opinion about
``-c:v`` it has become the second muvid, and the ``-f null -`` invariant that
keeps the package honest would have nothing left to protect.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Optional, Sequence

from looks.geometry import Size, ffmpeg_chain, placement, social_size
from looks.licence import Terms, terms_for
from looks.params import (
    COLORBALANCE_ZONES,
    CURVES_CHANNELS,
    EFFECT_PARAMS,
)
from looks.registry import REGISTRY, EffectRegistry
from looks.spec import ImplRef, LookPlan, Span, SpecError

#: Characters the **option** parser gives meaning to, within one filter's
#: arguments. Must lead with ``\\``: the backslashes introduced for the later
#: characters must not themselves be escaped by the ``\\`` pass.
OPTION_LEVEL_SPECIALS = ("\\", "'", ":")

#: Characters the **filtergraph** parser gives meaning to across the graph:
#: ``,`` chains, ``;`` separates, ``[]`` delimit pad labels, ``\\`` and ``'``
#: do that parser's quoting.
GRAPH_LEVEL_SPECIALS = ("\\", "'", ",", ";", "[", "]")


class FfmpegBackendError(SpecError):
    """A step that cannot be expressed as a filter fragment."""


def _backslash_escape(value: str, specials: Sequence[str]) -> str:
    for char in specials:
        value = value.replace(char, "\\" + char)
    return value


def escape_filter_value(value: str) -> str:
    r"""Escape a value for use as a filter option inside a filtergraph.

    >>> escape_filter_value("plain.cube")
    'plain.cube'

    A comma would end the filter and a colon would end the option, so both are
    escaped twice — once for each parser that will read them:

    >>> escape_filter_value("id,with:comma.cube")
    'id\\,with\\\\:comma.cube'

    ``%`` is left alone, on purpose — neither parser treats it as special, so
    escaping it only produced a backslash that was unescaped away again:

    >>> escape_filter_value("100%.cube")
    '100%.cube'
    """
    return _backslash_escape(
        _backslash_escape(value, OPTION_LEVEL_SPECIALS), GRAPH_LEVEL_SPECIALS
    )


def filter_string(name: str, options: Optional[Mapping[str, Any]] = None) -> str:
    r"""One filter, with its options escaped.

    >>> filter_string("gblur", {"sigma": 2})
    'gblur=sigma=2'
    >>> filter_string("null")
    'null'

    A path with a comma in it survives, which is the whole point:

    >>> filter_string("lut3d", {"file": "a,b.cube"})
    'lut3d=file=a\\,b.cube'
    """
    if not options:
        return name
    parts = [
        f"{key}={escape_filter_value(str(value))}"
        for key, value in options.items()
        if value is not None
    ]
    return f"{name}={':'.join(parts)}" if parts else name


def gated(fragment: str, at: Optional[Span]) -> str:
    """Restrict a fragment to a span, using ffmpeg's own timeline support.

    >>> gated("gblur=sigma=2", None)
    'gblur=sigma=2'
    >>> gated("gblur=sigma=2", Span(1.0, 3.5))
    "gblur=sigma=2:enable='between(t,1,3.5)'"

    A fragment of several filters is gated **per filter**, because ``enable`` is
    an option on a filter and not on a chain — writing it once at the end would
    gate only the last one, silently:

    >>> gated("scale=2:2,crop=1:1", Span(0.0, 1.0))
    "scale=2:2:enable='between(t,0,1)',crop=1:1:enable='between(t,0,1)'"
    """
    if at is None or at.is_whole:
        # A Span open at BOTH ends (`Span.is_whole`) bounds nothing, so it is
        # not a gate. Emitting `enable=` for it would be a filter option that
        # always evaluates true — noise in the string and a lie in a diff.
        # `looks.spec.Step.time_varying` asks this exact question through the
        # same predicate, on purpose: one decision, shared rather than copied.
        return fragment
    if at.start is None:
        window = f"enable='lte(t,{_num(at.end)})'"
    elif at.end is None:
        window = f"enable='gte(t,{_num(at.start)})'"
    else:
        window = f"enable='between(t,{_num(at.start)},{_num(at.end)})'"
    return ",".join(
        f"{part}{':' if '=' in part else '='}{window}"
        for part in split_filters(fragment)
    )


def split_filters(fragment):
    r"""A chain into its filters, splitting on UNESCAPED commas only.

    A comma inside a filter option is escaped — rule 21, and this package's own
    :func:`escape_filter_value` produces it routinely. Splitting on every comma
    cuts *inside* an expression: the shipped ``gamma`` effect compiles to
    ``lutrgb=r=maxval*pow(val/maxval\,0.833333):...``, and the naive split
    turned that into an unparseable chain the moment it was gated —
    ``pow(val/maxval\:enable='between(t,1,2)',0.83)``.

    >>> split_filters("scale=2:2,crop=1:1")
    ['scale=2:2', 'crop=1:1']

    An escaped comma stays inside its filter:

    >>> split_filters(r"lutrgb=r=pow(val\,2),gblur=sigma=1") == [
    ...     r"lutrgb=r=pow(val\,2)", "gblur=sigma=1"]
    True

    An escaped BACKSLASH does not escape the comma after it:

    >>> split_filters("a=x\\\\,b=y") == ["a=x\\\\", "b=y"]
    True
    """
    parts, current, backslashes = [], [], 0
    for char in fragment:
        if char == "," and backslashes % 2 == 0:
            parts.append("".join(current))
            current, backslashes = [], 0
            continue
        backslashes = backslashes + 1 if char == "\\" else 0
        current.append(char)
    parts.append("".join(current))
    return parts


def _num(value: float) -> str:
    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text or "0"


def vf(plan: LookPlan, *, gate: bool = True) -> str:
    """A whole plan as one ``-vf`` fragment: input-index-free, splice-ready.

    The seam every consumer asked for is one string — ``muvid`` splices it into
    the filter chain ``_render_part`` already builds, and that only works if
    nothing here names a stream.

    Raises:
        FfmpegBackendError: If a step is not ffmpeg-backed, or is gated to a
            span its filter cannot honour. The second is why
            :attr:`~looks.spec.ImplRef.timeline` exists: ``zoompan`` and
            ``elbg`` carry no timeline support, so an ``at`` on them would be
            accepted by the string and ignored by the binary.
    """
    fragments = []
    in_rgb_run = False
    wrap = _matrix_wrap(plan.clip)
    for index, step in enumerate(plan.steps):
        if step.impl.backend != "ffmpeg":
            raise FfmpegBackendError(
                f"step {index} ({step.effect!r}) runs on "
                f"{step.impl.backend!r}, which has no filter form. A plan "
                "mixing backends is compiled per backend, never flattened."
            )
        fragment = step.payload.get("filter")
        if not fragment:
            from looks.cache import PENDING

            if PENDING in step.payload:
                raise FfmpegBackendError(
                    f"step {index} ({step.effect!r}) needs an artifact that has "
                    f"not been built: cube {step.payload[PENDING]['key'][:12]}…. "
                    "Call looks.materialize(plan) first — compiling writes no "
                    "files on purpose, so acquiring artifacts is its own step."
                )
            raise FfmpegBackendError(
                f"step {index} ({step.effect!r}) has no 'filter' in its payload"
            )
        if step.at is not None and gate:
            if not step.impl.timeline:
                raise FfmpegBackendError(
                    f"step {index} ({step.effect!r}) is gated to {step.at}, but "
                    f"{step.impl.impl!r} has no timeline support — ffmpeg would "
                    "accept the option and ignore it, which is a look that "
                    "silently applies everywhere."
                )
            fragment = gated(fragment, step.at)
        if wrap:
            rgb = bool(RGB_DOMAIN_FILTERS & set(step.impl.requires_filters))
            if rgb != in_rgb_run:
                fragments.append(wrap)
                in_rgb_run = rgb
        fragments.append(fragment)
    if in_rgb_run:
        fragments.append(wrap)
    return ",".join(fragments)


#: Filters that only take RGB, so ffmpeg converts YUV to RGB and back around
#: them. On ffmpeg 6.1 that auto-inserted conversion ignores the colour tags:
#: a flat BT.709 frame lost about 7 luma through any of these, a colour test
#: pattern 6.4 mean luma (against 0.16 on ffmpeg 9), issue #29. A YUV-capable
#: filter (`lutyuv`, `gblur`) is untouched by it and so is not listed.
RGB_DOMAIN_FILTERS = frozenset(
    {"lutrgb", "colorchannelmixer", "colorbalance", "colorlevels", "curves", "lut3d"}
)

#: ClipSpec.color_space (the tag's name) -> scale's matrix name, where they differ.
_SCALE_MATRICES = {
    "bt709": "bt709",
    "bt601": "bt601",
    "smpte170m": "smpte170m",
    "bt470bg": "bt470",
    "bt2020nc": "bt2020",
    "smpte240m": "smpte240m",
    "fcc": "fcc",
}
_SCALE_RANGES = {
    "tv": "limited",
    "limited": "limited",
    "mpeg": "limited",
    "pc": "full",
    "full": "full",
    "jpeg": "full",
}


def _matrix_wrap(clip) -> Optional[str]:
    """The ``scale`` that makes a YUV<->RGB conversion use the clip's own matrix.

    Rule 24's mechanism: declare the matrix instead of trusting ffmpeg to read
    the tag. Placed on either side of each run of RGB-only steps, it is where
    that conversion happens (ffmpeg's negotiation moves it into the ``scale``),
    and costs nothing where the two sides already agree. **Absent** when the
    clip does not say its colour space: the conversion is then left to ffmpeg,
    which is what it always was. Rule 22 would refuse there, and refusing is
    not built yet.

    >>> from looks.spec import ClipSpec
    >>> _matrix_wrap(ClipSpec(width=2, height=2, fps=1, color_space="bt709"))
    'scale=in_color_matrix=bt709:out_color_matrix=bt709'
    >>> _matrix_wrap(ClipSpec(width=2, height=2, fps=1, color_space="bt709", color_range="pc"))
    'scale=in_color_matrix=bt709:out_color_matrix=bt709:in_range=full:out_range=full'
    >>> _matrix_wrap(ClipSpec(width=2, height=2, fps=1)) is None
    True
    """
    if clip is None or clip.color_space not in _SCALE_MATRICES:
        return None
    matrix = _SCALE_MATRICES[clip.color_space]
    options = {"in_color_matrix": matrix, "out_color_matrix": matrix}
    if clip.color_range in _SCALE_RANGES:
        range_ = _SCALE_RANGES[clip.color_range]
        options |= {"in_range": range_, "out_range": range_}
    return filter_string("scale", options)


# ---------------------------------------------------------------- the effects


def _ffmpeg_terms() -> Terms:
    """The static declaration. :func:`looks.compile.compile_look` replaces it
    with the probed binary's, which is the one that decides a tier."""
    return terms_for("ffmpeg")[0]


def _target_size(params: Mapping[str, Any]) -> Size:
    target = params.get("target")
    if target is None:
        raise FfmpegBackendError(
            "a geometry effect needs a 'target' — a size like '1920x1080' or a "
            "preset name like 'shorts'"
        )
    if isinstance(target, Size):
        return target
    text = str(target)
    if "x" in text.lower():
        width, height = text.lower().split("x", 1)
        return Size(int(width), int(height))
    return social_size(text)


def _geometry(mode: str):
    def compiler(params, *, clip=None, env=None, **_kw):
        if clip is None:
            raise FfmpegBackendError(
                f"the {mode!r} effect is derived from the source's size, so it "
                "needs a ClipSpec. Pass clip= to compile_look()."
            )
        target = _target_size(params)
        place = placement(Size(clip.width, clip.height), target, mode=mode)
        # `out_size` is a CONTRACT, not decoration: a pipe declares the frame
        # size its consumer must read, and rawvideo has no header to correct a
        # wrong guess. Any implementation that changes the frame's geometry has
        # to say so here or the pipe's declared stride is a lie.
        return {
            "filter": ffmpeg_chain(place) or "null",
            "out_size": [target.width, target.height],
        }

    return compiler


def _simple(name: str, build):
    def compiler(params, **_kw):
        return {"filter": filter_string(name, build(params))}

    return compiler


def _box_radius(sigma: float) -> int:
    """The ``boxblur`` radius whose spread matches a Gaussian of ``sigma``.

    A box of radius ``r`` is ``2r + 1`` wide, with variance ``((2r+1)**2 - 1)/12``;
    solving that for ``sigma**2`` gives the radius.

    >>> [_box_radius(s) for s in (0, 1, 2, 5)]
    [0, 1, 3, 8]
    """
    return round((math.sqrt(12 * sigma * sigma + 1) - 1) / 2)


def _boxblur_compiler(params, *, clip=None, **_kw):
    """``boxblur`` at the radius that matches ``gblur``'s spread.

    ``luma_power=1``: ffmpeg's default of 2 applies the box twice, which is
    about 1.41x wider than the Gaussian it stands in for (measured: sigma 5
    gave a spread of 6.93 against gblur's 4.90; with one pass, 4.90).

    ``boxblur`` refuses a radius of a quarter of the smaller side or more
    (chroma is half-size, and its bound is half of that). The schema cannot see
    the frame, so the bound is checked here, where ``gblur`` has none.

    >>> _boxblur_compiler({"sigma": 2})["filter"]
    'boxblur=luma_radius=3:luma_power=1'
    """
    radius = _box_radius(params["sigma"])
    if clip is not None and radius >= min(clip.width, clip.height) // 4:
        raise FfmpegBackendError(
            f"blur sigma {params['sigma']} needs a box radius of {radius}, which "
            f"boxblur refuses on a {clip.width}x{clip.height} frame (it must be "
            "under a quarter of the smaller side). Use a smaller sigma, or "
            "gblur, which has no such bound."
        )
    return {
        "filter": filter_string("boxblur", {"luma_radius": radius, "luma_power": 1})
    }


def _gamma_expression(params) -> Mapping[str, Any]:
    """Gamma through `lutrgb`, because rule 13 forbids the offset alternative.

    **``gamma > 1`` brightens**, the ``eq`` convention: the curve is
    ``pow(val/maxval, 1/gamma)``, so a mid-grey rises as ``gamma`` grows.

    An additive brightness offset lifts the black floor and reads as haze; a
    gamma curve keeps the endpoints. ``eq=gamma=`` would say this in one option
    and is GPL-only, so the LGPL form composes the same curve as a lookup.
    """
    gamma = float(params["gamma"])
    curve = f"maxval*pow(val/maxval,{1 / gamma:.6f})"
    return {"r": curve, "g": curve, "b": curve}


def _posterize_expression(params) -> Mapping[str, Any]:
    """Quantise through `lutrgb`, not `elbg`.

    ``elbg`` is ffmpeg's own posterizer and is **non-deterministic**: measured
    while building the flicker classifier, two runs of one command disagreed by
    70-86/255. A look that differs from itself between renders is not a look.
    """
    levels = int(params["levels"])
    step = f"round(val*{levels - 1}/maxval)*maxval/{levels - 1}"
    return {"r": step, "g": step, "b": step}


def _gradient_map_compiler(params, **_kw):
    """A ramp in, a cube REQUEST out — never a file.

    `compile_look` writes nothing, so this emits the artifact's address and the
    spec that reproduces it, and :func:`looks.cache.materialize` supplies the
    file. That is what keeps a compiled plan portable: it can be hashed, stored
    and sent to another machine, which then builds the same cube from the same
    spec and gets the same bytes.
    """
    from looks.cache import PENDING
    from looks.lut import DFLT_CUBE_SIZE, DFLT_CUBE_TITLE, Ramp, cube_key, gradient_map

    stops = params.get("stops")
    if not stops:
        raise FfmpegBackendError(
            "the 'gradient_map' effect needs 'stops': [(L*, '#rrggbb'), ...] — "
            "the ramp the look maps luminance onto"
        )
    size = int(params.get("size", DFLT_CUBE_SIZE))
    title = params.get("title", DFLT_CUBE_TITLE)
    spec = gradient_map(
        Ramp.from_hex([tuple(s) for s in stops]),
        contrast=float(params["contrast"]),
        lift=float(params["lift"]),
    )
    request = {
        "stops": [list(s) for s in stops],
        "size": size,
        "title": title,
        "contrast": float(params["contrast"]),
        "lift": float(params["lift"]),
        "key": cube_key(spec, size=size, title=title),
        # The template rather than the filter, because the path is not known
        # until the artifact exists. `{file}` is filled in by materialize with
        # an ESCAPED path — the flagship effect takes a caller-supplied
        # directory, and a comma in it would otherwise end the filter.
        "filter_template": "lut3d=file={file}:interp=" + params["interp"],
    }
    return {PENDING: request}


def register_defaults(registry: Optional[EffectRegistry] = None) -> EffectRegistry:
    """Register the built-in ffmpeg effects. Idempotent per registry.

    Called once on ``import looks``. Pass your own registry to get an
    independent set — the module-level default is the one
    :func:`looks.compile.compile_look` uses.

    Examples:
        >>> reg = register_defaults(EffectRegistry())
        >>> "saturation" in reg.effects() and "lut3d" in reg.effects()
        True

        Both ways to saturate are registered, and the LGPL one sorts first:

        >>> [i.impl for i in reg.implementations("saturation")]
        ['saturation.ffmpeg.colorchannelmixer', 'saturation.ffmpeg.eq']
    """
    reg = REGISTRY if registry is None else registry
    if "lut3d.ffmpeg.default" in reg:
        return reg
    terms = _ffmpeg_terms()
    for effect, schema in EFFECT_PARAMS.items():
        # A registry that declared its own schema for an effect keeps it.
        if not reg.has_params(effect):
            reg.declare_params(effect, schema)

    def add(
        key,
        filters,
        compiler,
        *,
        time_varying,
        preference=0,
        timeline=True,
        tags=(),
    ):
        # `time_varying` has no default, deliberately: `ImplRef.time_varying`
        # is unknown (`None`) unless declared, and unknown is not the same
        # claim as "does not read the clock". Forcing every built-in
        # registration to say which is how this module avoids shipping a
        # silent `False` for something nobody checked.
        effect, backend, _variant = key.split(".")
        reg.register(
            ImplRef(
                effect=effect,
                impl=key,
                backend=backend,
                terms=terms,
                requires_filters=filters,
                preference=preference,
                timeline=timeline,
                time_varying=time_varying,
            ),
            compiler,
            tags=tags,
        )

    # --- colour, LGPL first -------------------------------------------------
    add(
        "gradient_map.ffmpeg.lut3d",
        ("lut3d",),
        _gradient_map_compiler,
        time_varying=False,
    )
    add(
        "lut3d.ffmpeg.default",
        ("lut3d",),
        _simple(
            "lut3d",
            lambda p: {"file": p["cube"], "interp": p["interp"]},
        ),
        time_varying=False,
    )
    add(
        "saturation.ffmpeg.colorchannelmixer",
        ("colorchannelmixer",),
        _simple("colorchannelmixer", _saturation_matrix),
        time_varying=False,
    )
    add(
        "saturation.ffmpeg.eq",
        ("eq",),
        _simple("eq", lambda p: {"saturation": p["amount"]}),
        preference=1,
        tags=("gpl-gated",),
        time_varying=False,
    )
    add(
        "contrast.ffmpeg.lutyuv",
        ("lutyuv",),
        _simple("lutyuv", _contrast_luma),
        time_varying=False,
    )
    add(
        "contrast.ffmpeg.eq",
        ("eq",),
        _simple("eq", lambda p: {"contrast": p["amount"]}),
        preference=1,
        tags=("gpl-gated",),
        time_varying=False,
    )
    add(
        "gamma.ffmpeg.lutrgb",
        ("lutrgb",),
        _simple("lutrgb", _gamma_expression),
        time_varying=False,
    )
    add(
        "levels.ffmpeg.colorlevels",
        ("colorlevels",),
        _simple(
            "colorlevels",
            lambda p: {
                "rimin": p["black"],
                "gimin": p["black"],
                "bimin": p["black"],
                "rimax": p["white"],
                "gimax": p["white"],
                "bimax": p["white"],
            },
        ),
        time_varying=False,
    )
    add(
        "posterize.ffmpeg.lutrgb",
        ("lutrgb",),
        _simple("lutrgb", _posterize_expression),
        time_varying=False,
    )
    add(
        "flatten.ffmpeg.bilateral",
        ("bilateral",),
        _simple(
            "bilateral",
            lambda p: {
                "sigmaS": p["spatial"],
                "sigmaR": p["range"],
                # All three planes. bilateral's default is 1 — luma only — which
                # smooths the detail and leaves behind the chroma noise the
                # flatten was for.
                "planes": p["planes"],
            },
        ),
        time_varying=False,
    )

    # --- spatial ------------------------------------------------------------
    add(
        "blur.ffmpeg.gblur",
        ("gblur",),
        _simple("gblur", lambda p: {"sigma": p["sigma"]}),
        time_varying=False,
    )
    add(
        "blur.ffmpeg.boxblur",
        ("boxblur",),
        _boxblur_compiler,
        preference=1,
        tags=("gpl-gated",),
        time_varying=False,
    )
    add(
        "sharpen.ffmpeg.unsharp",
        ("unsharp",),
        _simple(
            "unsharp",
            # `luma_amount`, not `amount`: unsharp has no such option and
            # ffmpeg answers "Option not found" at configure time. Caught by
            # the registry sweep, which is what that sweep is for.
            lambda p: {"luma_amount": p["amount"]},
        ),
        time_varying=False,
    )

    # --- geometry, wrapping looks.geometry ----------------------------------
    for mode in ("fit", "fill", "stretch"):
        # timeline=False: `scale` and `pad` have NO timeline support, and ffmpeg
        # refuses the graph outright ("Timeline ('enable' option) not supported
        # with filter 'scale'"). Declaring True defeated `vf()`'s own guard with
        # its own registry data — the refusal existed and never fired, and the
        # binary rejected the command instead. A gated geometry step is now
        # refused at SELECTION, which is where a caller can act on it.
        add(
            f"{mode}.ffmpeg.scale",
            ("scale",),
            _geometry(mode),
            timeline=False,
            time_varying=False,
        )

    # --- motion, wrapping looks.motion --------------------------------------
    add(
        "motion.ffmpeg.crop",
        ("crop", "setpts"),
        _motion_compiler,
        timeline=False,
        # `zoompan`/`crop` compile to expressions that reference `in_time` —
        # the one implementation registered here that reads the clock
        # regardless of any Effect.at span. See issue #17: `timeline=False`
        # (above) answers "can it be gated to a span", which is a different
        # and close-to-inverse question.
        time_varying=True,
    )

    # --- film: grade, optical, grain (issue #25) ----------------------------
    # The catalogue's stage order is geometry -> grade -> look -> optical ->
    # grain; `looks` composes in the order asked and does not reorder.
    add("curves.ffmpeg.curves", ("curves",), _curves_compiler, time_varying=False)
    add(
        "colorbalance.ffmpeg.colorbalance",
        ("colorbalance",),
        _colorbalance_compiler,
        time_varying=False,
    )
    add(
        "vignette.ffmpeg.vignette",
        ("vignette",),
        _simple(
            "vignette",
            lambda p: {"angle": _num(float(p["angle"]))},
        ),
        time_varying=False,
    )
    add(
        "halation.ffmpeg.blend",
        ("format", "split", "colorchannelmixer", "lutrgb", "gblur", "blend"),
        _halation_compiler,
        # A branch: `split` has no timeline support, and `gated()` gates every
        # filter of a fragment, so a span is refused at selection instead.
        timeline=False,
        time_varying=False,
    )
    add(
        "grain.ffmpeg.noise",
        ("noise",),
        _grain_compiler,
        # The `t` flag re-draws the noise every frame — the catalogue's INDEXED
        # class. Deterministic for a fixed seed, and it reads the clock, which
        # is exactly what `time_varying` is for (issue #17).
        time_varying=True,
    )
    add(
        "gate_weave.ffmpeg.crop",
        ("crop", "scale", "setsar"),
        _gate_weave_compiler,
        timeline=False,
        time_varying=True,
    )
    return reg


def _saturation_matrix(params) -> Mapping[str, Any]:
    """Saturation as a scaled luma-preserving matrix.

    The LGPL answer to ``eq=saturation=``. Rec.709 luma coefficients, so a
    fully desaturated result is the same grey the encoder would compute.

    Note the recorded trap from `muvid`: ``colorchannelmixer`` is a silent
    no-op on YUV, so a caller wanting it on YUV input must convert first.
    """
    amount = float(params["amount"])
    lr, lg, lb = 0.2126, 0.7152, 0.0722
    cell = lambda base, weight: f"{weight + amount * (base - weight):.6f}"  # noqa: E731
    return {
        "rr": cell(1, lr),
        "rg": cell(0, lg),
        "rb": cell(0, lb),
        "gr": cell(0, lr),
        "gg": cell(1, lg),
        "gb": cell(0, lb),
        "br": cell(0, lr),
        "bg": cell(0, lg),
        "bb": cell(1, lb),
    }


def _contrast_luma(params) -> Mapping[str, Any]:
    r"""Contrast as a linear remap of LUMA: ``y = 128 + a(val - 128)``, clipped.

    The LGPL answer to ``eq=contrast=``, and it must agree with it — the two are
    implementations of one effect chosen by licence tier, so a caller who cannot
    use GPL must not get a different picture (rule 29b).

    **On the same plane, which is the whole point.** ``eq`` adjusts the luma
    plane and leaves chroma alone. Anything that works per RGB channel — the
    original ``curves=all=``, and the ``colorlevels`` that briefly replaced it —
    changes SATURATION as it changes contrast, so it agrees on grey and diverges
    on everything else. Measured against ``eq`` on a colour test pattern:

    ========  ==============  ==========
    amount    ``colorlevels``  ``lutyuv``
    ========  ==============  ==========
    0.5       74/255          2/255
    1.5       77/255          2/255
    2.0       134/255         2/255
    3.0       178/255         2/255
    ========  ==============  ==========

    On a grey ramp both are within 5 **through amount <= 2** (measured: 1, 4, 5
    at 0.5, 1.5, 2.0; the per-channel form widens to 9 at amount 3 and 26 at
    10). That narrow agreement on grey is why a greyscale-only test suite called
    the per-channel version interchangeable and shipped it. The tests now render
    colour, and compare all three channels rather than one.

    Verified equally on **limited-range** input (``scale=out_range=limited``),
    where a luma pivot could have gone wrong and does not: still within 2/255.

    A LUT, not a spline, so it also carries none of the three defects the
    original ``curves`` form had — no ringing (rule 26), no degenerate clamp,
    and no eased clip corner. Zero non-monotone steps at every amount measured.

    >>> _contrast_luma({"amount": 1.0})["y"]
    'clip(128+1*(val-128),0,255)'
    >>> _contrast_luma({"amount": 1.5})["y"]
    'clip(128+1.5*(val-128),0,255)'
    """
    # The non-negativity of `amount` is an EFFECT-level constraint and lives in
    # `looks.params.EFFECT_PARAMS`, not here: a check inside one compiler
    # is a check the licence tier can switch off.
    amount = float(params["amount"])
    # `%g` so 1.0 stays "1" and 1.5 stays "1.5": the expression reaches the
    # plan hash, and an amount that round-trips through a float repr would make
    # two identical Looks hash differently.
    return {"y": f"clip(128+{amount:g}*(val-128),0,255)"}


def _motion_compiler(params, *, clip=None, env=None, **_kw):
    """A camera path, via :mod:`looks.motion`.

    The registry entry that makes RULE G's compile half reachable from a
    ``Look``, so a camera move is a step in a plan like any other rather than a
    separate call a caller has to remember to make.
    """
    from looks.geometry import Size as _Size
    from looks.motion import Keyframe, Window, compile_motion

    frames = params.get("keyframes")
    if not frames:
        raise FfmpegBackendError(
            "the 'motion' effect needs 'keyframes': [(t, (x, y, w, h)), ...] in "
            "burns' normalised convention"
        )
    path = [
        Keyframe(float(t), Window(*(float(v) for v in window))) for t, window in frames
    ]
    output = None
    if params.get("output") is not None:
        output = _target_size({"target": params["output"]})
    elif clip is not None:
        output = _Size(clip.width, clip.height)
    fps = params.get("fps", clip.fps if clip is not None else None)
    payload = {"filter": compile_motion(path, output=output, fps=fps)}
    if output is not None:
        payload["out_size"] = [output.width, output.height]
    return payload


# ------------------------------------------------------------ the film effects
#
# Defaults are the effect catalogue's (docs/research/13 §3) unless noted; the
# halation tint and the gate weave are the 2026-10-16 production's (issue #25),
# where they read as 16 mm at 720p.

#: `setsar`'s largest allowed rational term. Its default of 100 rewrites any
#: SAR with a bigger term (118/81 -> 67/46, 1001/1000 -> 1/1).
SETSAR_MAX = 2**31 - 1

#: Prefix of the pad labels a branching effect uses internally, so they stay
#: clear of a host's own (``[a]``, ``[bg]``: note 05, label rule 2).
LABEL_NAMESPACE = "lk_"


def _curve_points(points) -> str:
    """``[(0, 0.03), (1, 0.95)]`` -> ``'0/0.03 1/0.95'``."""
    return " ".join(f"{_num(float(x))}/{_num(float(y))}" for x, y in points)


def _curves_compiler(params, **_kw):
    """Per-channel tone curves, always ``interp=pchip``.

    ``curves`` defaults to a natural cubic spline, which overshoots at a knee —
    21 non-monotone steps out of 255 on a steep curve, against 0 under pchip
    (rule 26, measured in the catalogue). Points are ``(x, y)`` pairs in 0..1.

    >>> _curves_compiler({"all": [(0, 0.03), (0.5, 0.47), (1, 0.95)]})["filter"]
    'curves=all=0/0.03 0.5/0.47 1/0.95:interp=pchip'
    """
    options = {
        channel: _curve_points(params[channel])
        for channel in CURVES_CHANNELS
        if params.get(channel)
    }
    if not options:
        raise FfmpegBackendError(
            f"the 'curves' effect needs points for at least one of "
            f"{list(CURVES_CHANNELS)}: [(x, y), ...] in 0..1"
        )
    return {"filter": filter_string("curves", {**options, "interp": "pchip"})}


def _colorbalance_compiler(params, **_kw):
    """Shadow / midtone / highlight RGB shifts, each in -1..1.

    >>> from looks.params import with_defaults
    >>> params = with_defaults("colorbalance", {"shadows": (-0.03, 0, 0.04)})
    >>> _colorbalance_compiler(params)["filter"]
    'colorbalance=rs=-0.03:gs=0:bs=0.04:rm=0:gm=0:bm=0:rh=0:gh=0:bh=0:pl=0'
    """
    options = {}
    for zone, letter in COLORBALANCE_ZONES.items():
        for channel, shift in zip("rgb", params[zone]):
            options[f"{channel}{letter}"] = _num(float(shift))
    options["pl"] = int(params["preserve_lightness"])
    return {"filter": filter_string("colorbalance", options)}


def _halation_compiler(params, **_kw):
    """Highlights, tinted and blurred, screened back over the picture.

    A branch, so it carries pad labels — under :data:`LABEL_NAMESPACE`, and
    the same ones every time. Two halations in one chain do not collide:
    ffmpeg binds a label to the next use of it in parse order, so a label
    that is opened and closed inside one fragment is free again after it
    (measured on 9.0 and 6.1: pixel-identical to per-step labels). The
    fragment still comma-splices, because its first and last pads are
    unlabelled. **Forced to RGB**
    (``format=gbrp16le``) because a ``screen`` blend negotiated in YUV screens the
    chroma planes too: measured on ``testsrc2``, the unforced form *lowered*
    mean green by 26/255 — a screen that darkens. In RGB it only ever adds.
    Sixteen bits, not ``gbrp``: a bare 8-bit format is what rule 23 forbids —
    on a 10-bit ramp ``gbrp`` kept 19 of 64 codes — and at 720p the 16-bit
    branch measured no slower (11-13 against 14-16 ms/frame).

    The mask is Rec.709 luma, thresholded per channel — the channels are equal
    after the grey matrix, so that is a luma threshold — and scaled by the tint
    in the same lookup, since a blur commutes with a per-channel gain.

    ``amount`` is folded into that gain, not passed as ``all_opacity``:
    ``screen(A, k*B)`` *is* ``A + k*(screen(A, B) - A)`` (within 1/65535,
    measured), so the blend runs at opacity 1. The opacity path was wrong on
    CI's ffmpeg 6.1.1 at 16 bits — an identity halation moved pixels by 129/255,
    and ``amount=0.5`` glowed more than ``amount=1`` — while 6.1.6 and 9.0 were
    exact.
    """
    threshold = float(params["threshold"])
    sigma = float(params["sigma"])
    amount = float(params["amount"])
    tint = params["tint"]
    a, b, h = (f"[{LABEL_NAMESPACE}{name}]" for name in "abh")
    mask = {
        channel: f"if(gt(val,{_num(threshold)}*maxval),val*{_num(amount * float(gain))},0)"
        for channel, gain in zip("rgb", tint)
    }
    branch = ",".join(
        (
            filter_string("colorchannelmixer", _saturation_matrix({"amount": 0.0})),
            filter_string("lutrgb", mask),
            filter_string("gblur", {"sigma": _num(sigma)}),
        )
    )
    screen = filter_string("blend", {"all_mode": "screen"})
    return {"filter": f"format=gbrp16le,split{a}{b};{b}{branch}{h};{a}{h}{screen}"}


def _grain_compiler(params, **_kw):
    """Temporal uniform noise: ``noise=alls=S:allf=t+u:all_seed=K``.

    Always temporal. Untagged ``noise`` is a fixed pattern, which reads as dirt
    on the lens rather than as grain, so there is no ``temporal`` switch — and
    one would make ``time_varying`` a function of the params, which an
    :class:`~looks.spec.ImplRef` declaration cannot express.

    >>> from looks.params import with_defaults
    >>> _grain_compiler(with_defaults("grain", {}))["filter"]
    'noise=alls=8:allf=t+u:all_seed=0'
    """
    return {
        "filter": filter_string(
            "noise",
            {
                "alls": int(params["strength"]),
                "allf": "t+u",
                "all_seed": int(params["seed"]),
            },
        )
    }


def _gate_weave_compiler(params, *, clip=None, **_kw):
    """A film gate's wander: a sinusoidal crop, scaled back to the input size.

    Reads ``t`` rather than the frame index, so the wander's speed does not
    change with the frame rate. The scale-back is a zoom of ``2A`` pixels,
    which is what a real gate's matte hides too. Two details, each measured
    (review of #27):

    - ``exact=1``: without it ``crop`` snaps to the chroma grid on 4:2:0, so
      the gate moved in 2-pixel steps (9 positions in 96 frames, not 24) and an
      odd 65x49 frame came back 64x48.
    - ``setsar`` undoes the aspect ``scale`` assigns to a non-uniform stretch
      (1920x1080 came out ``sar 4311:4304``, which a concat then refuses). It
      is written in the stream's own ``sar``/``w``/``h``, so it assumes no
      aspect and needs no ClipSpec; :data:`SETSAR_MAX` stops its default
      ``max=100`` approximating ``118/81`` as ``67/46``; and an unknown
      ``0/1`` is made ``1/1`` first, which every player reads it as anyway.

    >>> _gate_weave_compiler({"amplitude": 2, "frequency": (3, 2)})["filter"]
    'setsar=sar=sar:max=2147483647,crop=w=iw-4:h=ih-4:x=2+2*sin(2*PI*3*t):y=2+2*cos(2*PI*2*t):exact=1,scale=w=iw+4:h=ih+4,setsar=sar=sar*w*(h-4)/(h*(w-4)):max=2147483647'
    """
    amplitude = int(params["amplitude"])
    margin = 2 * amplitude
    if clip is not None and margin >= min(clip.width, clip.height):
        raise FfmpegBackendError(
            f"gate_weave amplitude {amplitude} leaves nothing of a "
            f"{clip.width}x{clip.height} frame: 2 * amplitude must be below its "
            "smaller side"
        )
    fx, fy = (_num(float(f)) for f in params["frequency"])
    crop = filter_string(
        "crop",
        {
            "w": f"iw-{margin}",
            "h": f"ih-{margin}",
            "x": f"{amplitude}+{amplitude}*sin(2*PI*{fx}*t)",
            "y": f"{amplitude}+{amplitude}*cos(2*PI*{fy}*t)",
            "exact": 1,
        },
    )
    scale = filter_string("scale", {"w": f"iw+{margin}", "h": f"ih+{margin}"})
    # An unknown SAR (0/1) is read as 1 by the inverse below, so it is made 1/1
    # first; otherwise it came out 99/100 and a concat with a 0/1 part failed.
    square_unknown = filter_string("setsar", {"sar": "sar", "max": SETSAR_MAX})
    # The inverse of scale's own SAR correction for (w-2A, h-2A) -> (w, h).
    restore = filter_string(
        "setsar",
        {"sar": f"sar*w*(h-{margin})/(h*(w-{margin}))", "max": SETSAR_MAX},
    )
    return {"filter": f"{square_unknown},{crop},{scale},{restore}"}
