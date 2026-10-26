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

from looks.compile import compile_look
from looks.environment import probe
from looks.ffmpeg import vf
from looks.spec import ClipSpec, Effect, Look

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


def _planes(fragment, source):
    chain = f"{fragment}," if fragment else ""
    return subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", source, "-vf",
         f"{chain}format=yuv420p", "-frames:v", "1", "-f", "rawvideo", "-"],
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


def test_an_undeclared_colour_space_is_left_to_ffmpeg(env):
    """Rule 22 would refuse; that is not built, and is the status quo."""
    fragment = _fragment(env, UNTAGGED, ("gamma", {"gamma": 1.0}))
    assert "color_matrix" not in fragment
