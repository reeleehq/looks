"""An RGB-only step must not shift the colour of tagged video (issue #29).

On ffmpeg 6.1 (what CI runs) the YUV<->RGB conversion ffmpeg inserts around
`curves`, `lutrgb`, `colorchannelmixer` and friends ignores the colour tags, so
a BT.709 frame came back about 6 luma darker; on ffmpeg 9 it did not. The fix
declares the matrix (`scale=in_color_matrix=..:out_color_matrix=..`) around each
run of such steps. These tests compare DECODED pixels, so the build that
matters is whichever one runs them.
"""

import shutil
import subprocess

import pytest

from looks.compile import CompileError, compile_look
from looks.environment import probe
from looks.ffmpeg import vf
from looks.spec import (
    ClipSpec,
    Effect,
    Look,
    plan_from_dict,
    plan_hash,
    plan_to_dict,
)

SIZE = (64, 48)
def _source(range_):
    return (
        f"smptehdbars=size={SIZE[0]}x{SIZE[1]}:rate=1,format=yuv420p,"
        f"setparams=colorspace=bt709:range={range_}:color_primaries=bt709:color_trc=bt709"
    )


def _clip(range_):
    return ClipSpec(
        width=SIZE[0], height=SIZE[1], fps=1, color_space="bt709", color_range=range_
    )


TAGGED = _clip("tv")
UNTAGGED = ClipSpec(width=SIZE[0], height=SIZE[1], fps=1)
#: ffmpeg 9 round-trips this source to within 0.16 mean luma; 6.1 without the
#: matrix is off by 6.4. Anything under this passes on every build.
TOLERANCE = 2.0
#: The effects whose implementations only take RGB, each as an identity.
RGB_EFFECTS = {
    "curves": {"all": [(0, 0), (1, 1)]},
    "gamma": {"gamma": 1.0},
    "saturation": {"amount": 1.0},
    "levels": {},
    "colorbalance": {"shadows": (0, 0, 0)},
}


def _planes(fragment, source, *, pix_fmt="yuv420p"):
    chain = f"{fragment}," if fragment else ""
    return subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", source, "-vf",
         f"{chain}format={pix_fmt}", "-frames:v", "1", "-f", "rawvideo", "-"],
        capture_output=True, check=True,
    ).stdout


@pytest.fixture(scope="module")
def env():
    e = probe()
    if not e.available or shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not usable")
    return e


def _fragment(env, clip, *names_params):
    steps = tuple(Effect(name=n, params=p) for n, p in names_params)
    return vf(compile_look(Look(steps=steps), clip=clip, env=env))


def _plane_drift(reference, after):
    luma = SIZE[0] * SIZE[1]
    chroma = luma // 4
    cuts = [(0, luma), (luma, luma + chroma), (luma + chroma, luma + 2 * chroma)]
    return [
        sum(abs(a - b) for a, b in zip(reference[i:j], after[i:j])) / (j - i)
        for i, j in cuts
    ]


@pytest.mark.parametrize("range_", ["tv", "pc"])
@pytest.mark.parametrize("effect", sorted(RGB_EFFECTS))
def test_an_identity_rgb_step_leaves_a_tagged_picture_alone(env, effect, range_):
    """All three planes (rule 29b: a luma-only check hides a chroma shift)."""
    source = _source(range_)
    fragment = _fragment(env, _clip(range_), (effect, RGB_EFFECTS[effect]))
    drift = _plane_drift(_planes("", source), _planes(fragment, source))
    assert max(drift) < TOLERANCE, (effect, range_, drift)


def test_the_pipe_path_declares_the_matrix_too(env):
    from looks.pipe import pipe_plan

    plan = compile_look(
        Look(steps=(Effect(name="gamma", params={"gamma": 1.0}),)),
        clip=TAGGED,
        env=env,
    )
    assert "in_color_matrix=bt709" in pipe_plan(plan, source="in.mp4").segments[0].vf


def test_a_run_of_rgb_steps_shares_one_conversion_pair(env):
    fragment = _fragment(
        env, TAGGED, ("gamma", {"gamma": 1.0}), ("curves", RGB_EFFECTS["curves"])
    )
    assert fragment.count("in_color_matrix=bt709") == 2


def test_a_yuv_step_between_two_rgb_runs_splits_them(env):
    fragment = _fragment(
        env,
        TAGGED,
        ("gamma", {"gamma": 1.0}),
        ("blur", {"sigma": 1}),
        ("curves", RGB_EFFECTS["curves"]),
    )
    assert fragment.count("in_color_matrix=bt709") == 4


def test_a_yuv_only_look_is_left_alone(env):
    assert "color_matrix" not in _fragment(env, TAGGED, ("blur", {"sigma": 1}))


def test_an_undeclared_colour_space_is_refused(env):
    """Rule 22: an RGB-only step on a clip of unknown colour space refuses."""
    with pytest.raises(CompileError, match="colour space"):
        _fragment(env, UNTAGGED, ("gamma", {"gamma": 1.0}))


def test_a_yuv_only_look_needs_no_declared_colour(env):
    assert "color_matrix" not in _fragment(env, UNTAGGED, ("blur", {"sigma": 1}))


def test_an_assumed_colour_space_is_declared_and_recorded(env):
    look = Look(steps=(Effect(name="gamma", params={"gamma": 1.0}),))
    assumed = compile_look(look, clip=UNTAGGED, env=env, assume_color_space="bt709")
    probed = compile_look(look, clip=TAGGED, env=env)
    assert assumed.clip.color_assumed and not probed.clip.color_assumed
    assert "in_color_matrix=bt709" in vf(assumed)
    assert plan_hash(assumed) != plan_hash(probed)
    assert plan_from_dict(
        plan_to_dict(assumed), impls={s.impl.impl: s.impl for s in assumed.steps}
    ).clip.color_assumed


def test_the_assumption_yields_to_a_declared_space(env):
    look = Look(steps=(Effect(name="gamma", params={"gamma": 1.0}),))
    plan = compile_look(look, clip=TAGGED, env=env, assume_color_space="bt601")
    assert plan.clip.color_space == "bt709" and not plan.clip.color_assumed


def test_assuming_with_no_clip_is_an_error(env):
    look = Look(steps=(Effect(name="gamma", params={"gamma": 1.0}),))
    with pytest.raises(CompileError, match="needs a clip"):
        compile_look(look, env=env, assume_color_space="bt709")

#: Sources with no hard colour edge and nothing outside the RGB gamut. On these a
#: 10-bit identity RGB step must be lossless; `smptehdbars` is not one of them
#: (issue #37): its edges are resampled by 4:2:0 <-> RGB and its PLUGE patches
#: are out of gamut, which no bit depth or matrix declaration recovers.
#: A gradient, not a flat colour: a flat 8-bit colour survives an 8-bit trip, so
#: only a ramp can see a narrowed intermediate.
SMOOTH_10BIT = {
    "gradient": (
        "gradients=s=64x48:r=1:speed=0.01:seed=3:c0=0x103060:c1=0xc08040"
        ":x0=0:y0=0:x1=64:y1=48:nb_colors=2"
    ),
}


def _samples_10bit(raw):
    return [int.from_bytes(raw[i : i + 2], "little") for i in range(0, len(raw), 2)]


@pytest.mark.parametrize("space", ["bt709", "bt2020nc"])
@pytest.mark.parametrize("kind", sorted(SMOOTH_10BIT))
@pytest.mark.parametrize("effect", sorted(RGB_EFFECTS))
def test_an_identity_rgb_step_is_lossless_on_smooth_10_bit(env, effect, kind, space):
    """Refutes issue #37's premise: no 8-bit intermediate costs a 10-bit source."""
    source = (
        f"{SMOOTH_10BIT[kind]},format=yuv420p10le,"
        f"setparams=colorspace={space}:range=tv"
    )
    clip = ClipSpec(
        width=SIZE[0], height=SIZE[1], fps=1, color_space=space, color_range="tv"
    )
    fragment = _fragment(env, clip, (effect, RGB_EFFECTS[effect]))
    before = _samples_10bit(_planes("", source, pix_fmt="yuv420p10le"))
    after = _samples_10bit(_planes(fragment, source, pix_fmt="yuv420p10le"))
    assert max(abs(a - b) for a, b in zip(before, after)) <= 1, (effect, kind, space)
