"""The parameter schema (issue #28): one declaration, read by checks and compilers.

Pure data plus `compile_look`'s refusal; no ffmpeg process is started except
where a test says so and skips without one.
"""

import math
import re
import shutil
import subprocess

import pytest

from looks.compile import CompileError, check_effect_params
from looks.params import (
    EFFECT_PARAMS,
    NO_DEFAULT,
    ParamError,
    check_params,
    with_defaults,
)
from looks.registry import REGISTRY
from looks.spec import Effect

ALL = [(e, p) for e, schema in sorted(EFFECT_PARAMS.items()) for p in sorted(schema)]
NUMERIC = [(e, p) for e, p in ALL if EFFECT_PARAMS[e][p].kind in ("real", "whole")]
VECTORS = [(e, p) for e, p in ALL if EFFECT_PARAMS[e][p].kind == "vector"]


@pytest.mark.parametrize("effect", REGISTRY.effects())
def test_every_registered_effect_has_a_schema(effect):
    """A new effect nobody declared would be silently unchecked."""
    with pytest.raises(ParamError, match="unknown parameter"):
        REGISTRY.check_params(effect, {"nonesuch": 1})


def test_the_schema_belongs_to_the_registry_not_the_package():
    """A registry with its own `flatten` is not bound to bilateral's keys."""
    from looks.registry import EffectRegistry

    other = EffectRegistry()
    other.check_params("flatten", {"scale": 3})  # undeclared: unchecked
    with pytest.raises(ParamError):
        REGISTRY.check_params("flatten", {"scale": 3})


@pytest.mark.parametrize("effect, key", ALL)
def test_a_declared_default_is_accepted_by_its_own_check(effect, key):
    param = EFFECT_PARAMS[effect][key]
    if param.default is not NO_DEFAULT:
        assert param.accepts(param.default), (effect, key, param.default)


@pytest.mark.parametrize("effect", sorted(EFFECT_PARAMS))
def test_an_unknown_key_is_refused_and_the_message_lists_the_known_ones(effect):
    with pytest.raises(CompileError, match="unknown parameter 'nonesuch'"):
        check_effect_params(Effect(name=effect, params={"nonesuch": 1}))


@pytest.mark.parametrize(
    "effect, params",
    [
        ("colorbalance", {"shadow": (0, 0, 0)}),  # singular: was an identity grade
        ("halation", {"sigmaa": 3}),
        ("grain", {"temporal": True}),
    ],
)
def test_the_misspellings_from_the_issue_are_refused(effect, params):
    with pytest.raises(CompileError, match=effect):
        check_effect_params(Effect(name=effect, params=params))


@pytest.mark.parametrize("effect, key", NUMERIC)
@pytest.mark.parametrize(
    "bad", [True, "0.5", math.inf, -math.inf, math.nan, None], ids=repr
)
def test_a_number_parameter_refuses_a_bool_a_string_and_a_non_finite(effect, key, bad):
    with pytest.raises(ParamError, match=key):
        check_params(effect, {key: bad})


@pytest.mark.parametrize("effect, key", VECTORS)
@pytest.mark.parametrize("bad", [True, "abc", math.inf, math.nan, (None,) * 3])
def test_a_vector_parameter_refuses_the_same_laxities(effect, key, bad):
    """`gate_weave` frequency `inf` compiled to `sin(2*PI*inf*t)`; ffmpeg exited 0."""
    with pytest.raises(ParamError, match=key):
        check_params(effect, {key: bad})


@pytest.mark.parametrize("bad", [True, "0/0 1/1", [(0, math.inf), (1, 1)], [(0, True), (1, 1)]])
def test_a_curve_refuses_the_same_laxities(bad):
    with pytest.raises(ParamError, match="all"):
        check_params("curves", {"all": bad})


def test_a_wrong_type_is_not_reported_as_a_bound():
    with pytest.raises(ParamError, match="must be a finite number"):
        check_params("contrast", {"amount": True})
    with pytest.raises(ParamError, match="must not be negative"):
        check_params("contrast", {"amount": -1})


def test_interp_is_one_of_ffmpegs():
    check_params("lut3d", {"interp": "nearest"})
    with pytest.raises(ParamError, match="interp"):
        check_params("lut3d", {"interp": "bogus"})


def test_a_black_point_below_zero_is_what_colorlevels_accepts():
    check_params("levels", {"black": -0.1})


def test_an_effect_without_a_schema_is_not_checked():
    check_params("a_callers_own_effect", {"anything": object()})


def test_defaults_fill_what_is_absent_and_leave_what_is_given():
    filled = with_defaults("halation", {"sigma": 3})
    assert filled["sigma"] == 3
    assert filled["threshold"] == EFFECT_PARAMS["halation"]["threshold"].default


def test_with_defaults_does_not_touch_its_input():
    given = {"sigma": 3}
    with_defaults("halation", given)
    assert given == {"sigma": 3}


def test_an_omitted_parameter_means_the_same_to_both_contrast_implementations():
    """Rule 29b: the default is the effect's, so it cannot differ per implementation."""
    assert with_defaults("contrast", {}) == {"amount": 1.0}


def test_the_plan_records_the_params_as_asked_not_with_defaults_filled_in():
    """Defaults are applied at compile time; `look_hash` and `Step.params` stay intent."""
    from looks.compile import compile_look
    from looks.environment import probe
    from looks.spec import ClipSpec, Look

    env = probe()
    if not env.available:
        pytest.skip("ffmpeg not usable")
    look = Look(steps=(Effect(name="grain"),))
    plan = compile_look(look, clip=ClipSpec(width=64, height=48, fps=10), env=env)
    assert dict(plan.steps[0].params) == {}
    assert "alls=8" in plan.steps[0].payload["filter"]


def test_a_stored_plans_params_are_enough_to_run_its_compiler():
    """`get_compiler(key)(step.params)` is how a plan becomes work again; the
    plan stores params as asked, defaults absent."""
    from looks.registry import get_compiler

    assert "alls=8" in get_compiler("grain.ffmpeg.noise")({})["filter"]


def test_both_blurs_read_the_same_parameter_and_agree_on_the_spread():
    """Rule 29b: the licence tier that picks the implementation must not pick the picture."""
    from looks.ffmpeg import _box_radius
    from looks.registry import get_compiler

    gauss = get_compiler("blur.ffmpeg.gblur")({"sigma": 5})["filter"]
    box = get_compiler("blur.ffmpeg.boxblur")({"sigma": 5})["filter"]
    assert "sigma=5" in gauss
    assert f"luma_radius={_box_radius(5)}" in box
    assert "luma_power=1" in box  # ffmpeg's default of 2 passes is 1.41x wider


def test_a_stored_plan_with_bad_params_is_refused_at_the_compiler():
    from looks.registry import get_compiler

    with pytest.raises(ParamError, match="levels"):
        get_compiler("posterize.ffmpeg.lutrgb")({"levels": 1})


def test_a_box_radius_ffmpeg_would_refuse_is_refused_here_first():
    from looks.ffmpeg import FfmpegBackendError
    from looks.registry import get_compiler
    from looks.spec import ClipSpec

    clip = ClipSpec(width=64, height=48, fps=10)
    boxblur = get_compiler("blur.ffmpeg.boxblur")
    boxblur({"sigma": 5}, clip=clip)
    with pytest.raises(FfmpegBackendError, match="gblur"):
        boxblur({"sigma": 50}, clip=clip)


def test_a_registry_that_declared_its_own_schema_keeps_it():
    from looks.ffmpeg import register_defaults
    from looks.params import real
    from looks.registry import EffectRegistry

    mine = EffectRegistry()
    mine.declare_params("blur", {"scale": real("scale", 1.0)})
    register_defaults(mine)
    mine.check_params("blur", {"scale": 2})
    with pytest.raises(ParamError):
        mine.check_params("blur", {"sigma": 2})


def test_the_two_blurs_have_the_same_spread_in_rendered_pixels():
    """Rule 29b on pixels, not on filter text: a vertical line through each, read along a row (a point source's tails quantise away)."""
    import shutil
    import subprocess

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not on PATH")
    from looks.registry import get_compiler

    def spread(key):
        fragment = get_compiler(key)({"sigma": 5})["filter"]
        source = "color=c=black:size=66x66:rate=1,drawbox=x=33:y=0:w=1:h=66:color=white:t=fill"
        raw = subprocess.run(
            ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", source, "-vf",
             f"format=gray,{fragment}", "-frames:v", "1", "-f", "rawvideo", "-"],
            capture_output=True, check=True,
        ).stdout
        row = raw[33 * 66 : 34 * 66]
        total = sum(row)
        mean = sum(i * v for i, v in enumerate(row)) / total
        return (sum(v * (i - mean) ** 2 for i, v in enumerate(row)) / total) ** 0.5

    assert abs(spread("blur.ffmpeg.gblur") - spread("blur.ffmpeg.boxblur")) < 0.5


# ---------------------------------------------- curves and the pixel format (#33)
#
# ffmpeg refuses two `curves` x-points that truncate to one code value of the
# format `curves` runs at: `(int)(x * (2**depth - 1))` must strictly increase.

#: Refused at 8 bits (127, 127), accepted at 10 (511, 512).
CLOSE_AT_8 = [(0, 0), (0.5, 0.5), (0.501, 0.6), (1, 1)]
#: Refused at 10 bits (511, 511), accepted at 16 (32767, 32787).
CLOSE_AT_10 = [(0, 0), (0.5, 0.5), (0.5003, 0.6), (1, 1)]
#: At ffmpeg's scale of 255 (not 256) both are code value 127, so refused at 8
#: bits; an off-by-one scale would put 0.5 at 128 and accept it.
ON_THE_8_BIT_SCALE = [(0, 0), (0.4999, 0.4), (0.5, 0.6), (1, 1)]
#: 0.5019605 is written 0.50196, which is 128.0 at 8 bits and so accepted; read
#: unrounded it is 128.00001 too, but 0.5019605 * 255 lands BELOW 128 once the
#: check forgets the six decimals the compiler writes.
AS_WRITTEN = [(0, 0), (0.5, 0.5), (0.5019605, 0.6), (1, 1)]
#: 0.0001 apart, yet in different 8-bit code values (0, 1): the rule truncates,
#: it does not measure distance, so this is accepted.
APART_BY_TRUNCATION = [(0.0039, 0), (0.004, 0.5), (1, 1)]


@pytest.mark.parametrize(
    "points, pix_fmt, refused",
    [
        (CLOSE_AT_8, "yuv420p", True),
        (CLOSE_AT_8, "yuv420p10le", False),
        (CLOSE_AT_10, "yuv420p10le", True),
        (CLOSE_AT_10, "yuv444p16le", False),
        (CLOSE_AT_10, "rgb48le", False),
        (APART_BY_TRUNCATION, "rgb24", False),
        (ON_THE_8_BIT_SCALE, "rgb24", True),
        (AS_WRITTEN, "rgb24", False),
    ],
)
def test_curves_refuses_points_in_one_code_value_of_the_format(
    points, pix_fmt, refused
):
    if refused:
        with pytest.raises(ParamError, match=f"one code value of {pix_fmt}"):
            check_params("curves", {"red": points}, pix_fmt=pix_fmt)
    else:
        check_params("curves", {"red": points}, pix_fmt=pix_fmt)


@pytest.mark.parametrize("pix_fmt", [None, "some_format_nobody_listed"])
def test_without_a_known_format_only_the_six_decimal_check_applies(pix_fmt):
    check_params("curves", {"all": CLOSE_AT_10}, pix_fmt=pix_fmt)
    with pytest.raises(ParamError, match="six decimals"):
        check_params(
            "curves", {"all": [(0, 0), (0.5, 0.5), (0.5000001, 1)]}, pix_fmt=pix_fmt
        )


def _clip(pix_fmt):
    from looks.spec import ClipSpec

    return ClipSpec(width=64, height=64, fps=10.0, pix_fmt=pix_fmt, color_space="bt709")


def _compile(env, steps, pix_fmt):
    from looks.compile import compile_look
    from looks.spec import Look

    return compile_look(Look(steps=steps), clip=_clip(pix_fmt), env=env)


@pytest.fixture(scope="module")
def env():
    from looks.environment import probe

    e = probe()
    if not e.available:
        pytest.skip("ffmpeg not usable")
    return e


def test_compile_look_refuses_on_an_8_bit_clip_and_accepts_on_10(env):
    curves = (Effect(name="curves", params={"all": CLOSE_AT_8}),)
    with pytest.raises(CompileError, match="one code value of yuv420p "):
        _compile(env, curves, "yuv420p")
    _compile(env, curves, "yuv420p10le")


def test_a_curves_after_another_step_is_not_depth_checked(env):
    """A later step's format is ffmpeg's negotiation, which nothing here knows."""
    steps = (
        Effect(name="levels", params={}),
        Effect(name="curves", params={"all": CLOSE_AT_8}),
    )
    _compile(env, steps, "yuv420p")


def _ffmpeg_accepts(fragment, pix_fmt) -> bool:
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not on PATH")
    source = f"testsrc2=size=64x64:rate=10:duration=0.1,format={pix_fmt}"
    argv = ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", source]
    argv += ["-vf", fragment, "-frames:v", "1", "-f", "null", "-"]
    return subprocess.run(argv, capture_output=True).returncode == 0


@pytest.mark.parametrize(
    "pix_fmt",
    [
        "yuv420p",
        "rgb24",
        "yuv420p10le",
        "p010le",
        "yuv422p12le",
        "yuv444p16le",
        "gray16le",
    ],
)
@pytest.mark.parametrize(
    "points", [CLOSE_AT_8, CLOSE_AT_10, APART_BY_TRUNCATION, ON_THE_8_BIT_SCALE, AS_WRITTEN]
)
def test_the_check_and_the_binary_agree(env, points, pix_fmt):
    """Run, not assumed: the refusal is ffmpeg's, at the depth ffmpeg negotiates."""
    from looks.ffmpeg import vf

    effect = Effect(name="curves", params={"all": points})
    try:
        _compile(env, (effect,), pix_fmt)
        refused_here = False
    except CompileError:
        refused_here = True
    fragment = vf(_compile(env, (effect,), None))  # the same chain, unchecked
    assert _ffmpeg_accepts(fragment, pix_fmt) is not refused_here


def _pix_fmt_depths() -> dict:
    """``ffmpeg -pix_fmts``: each format's deepest component, in bits."""
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-pix_fmts"], capture_output=True, text=True
    ).stdout
    depths = {}
    for line in out.splitlines():
        parts = line.split()
        if len(parts) == 5 and parts[3].isdigit():
            depths[parts[1]] = max(int(d) for d in parts[4].split("-"))
    return depths


def _negotiated_into_curves(env, pix_fmt, *, output_pix_fmt=None) -> str:
    """The format ffmpeg hands ``curves`` in ``vf``'s own chain, read by ``showinfo``."""
    from looks.ffmpeg import vf

    effect = Effect(name="curves", params={"all": [(0, 0), (1, 1)]})
    chain = vf(_compile(env, (effect,), pix_fmt))
    assert chain.count(":interp=pchip,") == 1, chain
    chain = chain.replace(":interp=pchip,", ":interp=pchip,showinfo,")
    argv = ["ffmpeg", "-hide_banner", "-v", "info", "-f", "lavfi"]
    argv += ["-i", f"testsrc2=size=64x64:rate=10:duration=0.1,format={pix_fmt}"]
    argv += ["-vf", chain]
    if output_pix_fmt:
        argv += ["-pix_fmt", output_pix_fmt]
    argv += ["-frames:v", "1", "-f", "null", "-"]
    run = subprocess.run(argv, capture_output=True, text=True)
    shown = re.search(r"fmt:(\S+)", run.stderr)
    assert shown, f"no showinfo line for {pix_fmt}: {run.stderr[-300:]}"
    return shown.group(1)


def test_every_listed_depth_is_the_one_curves_is_negotiated_to(env):
    """`CURVES_DEPTH` re-measured, every entry: what ffmpeg hands `curves`.

    Not the format's own component depth, which differs (`rgb565le` has 5- and
    6-bit components and `curves` runs it at 8).
    """
    from concurrent.futures import ThreadPoolExecutor

    from looks.params import CURVES_DEPTH

    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not on PATH")
    depths = _pix_fmt_depths()
    assert set(CURVES_DEPTH) <= set(depths), "a listed format this ffmpeg lacks"
    with ThreadPoolExecutor() as pool:
        got = dict(zip(CURVES_DEPTH, pool.map(lambda f: _negotiated_into_curves(env, f), CURVES_DEPTH)))
    assert {f: depths[g] for f, g in got.items()} == dict(CURVES_DEPTH)


@pytest.mark.parametrize("output_pix_fmt", ["yuv420p", "yuv420p10le", "rgb48le", "gbrp16le"])
def test_the_depth_holds_whatever_the_output_format_is(env, output_pix_fmt):
    """`vf`'s matrix ``scale`` on BOTH sides of ``curves`` is what pins it.

    Without the trailing one, an 8-bit source written as ``rgb48le`` ran
    ``curves`` at 16 bits and accepted what the 8-bit check refuses. Measured
    with the wrap on 6.1 and 9.0: the source's depth, for every output here.
    """
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not on PATH")
    for source, expected in (("yuv420p", "rgb24"), ("yuv420p10le", "gbrp10le")):
        got = _negotiated_into_curves(env, source, output_pix_fmt=output_pix_fmt)
        assert got == expected, (source, output_pix_fmt)
