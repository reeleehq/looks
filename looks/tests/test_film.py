"""The film effects of issue #25, checked on decoded pixels.

`test_ffmpeg.py` already sweeps every effect through the binary and
`test_time_varying.py` measures each one's clock-reading against its
declaration. This file asserts what each effect does to a **colour** picture,
on every channel (rule 29b's lesson: a grey ramp hides a per-channel bug), plus
the two mechanisms the effects brought with them — scoped pad labels for a
branching step, and effect-level parameter refusals.

Offline and free: every source is `lavfi`, every process ends in `-f null -` or
writes raw frames to stdout.
"""

import shutil
import subprocess

import pytest

from looks.compile import CompileError, compile_look
from looks.environment import probe
from looks.ffmpeg import vf
from looks.spec import ClipSpec, Effect, Look, Span, SpanUnsupported

SIZE = (64, 48)
CLIP = ClipSpec(width=SIZE[0], height=SIZE[1], fps=10)
COLOUR = f"testsrc2=size={SIZE[0]}x{SIZE[1]}:rate=10"
#: A colour bar pattern carries both shadows and highlights; testsrc2 alone is
#: mostly mid-tones and saturated primaries.
BARS = f"smptehdbars=size={SIZE[0]}x{SIZE[1]}:rate=10"


def _ffmpeg_or_skip():
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not on PATH")


@pytest.fixture(scope="module")
def env():
    e = probe()
    if not e.available:
        pytest.skip("ffmpeg not usable")
    return e


def _vf(env, *effects, **vf_kw):
    return vf(compile_look(Look(steps=effects), clip=CLIP, env=env), **vf_kw)


def frames(fragment, *, source=COLOUR, count=1):
    """``count`` decoded rgb24 frames, each a bytes object."""
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", source,
         "-vf", f"{fragment},format=rgb24", "-frames:v", str(count),
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr.decode("utf-8", "replace")[-600:]
    size = SIZE[0] * SIZE[1] * 3
    assert len(proc.stdout) == size * count, (len(proc.stdout), size * count)
    return [proc.stdout[i * size:(i + 1) * size] for i in range(count)]


def channel_means(frame):
    n = len(frame) // 3
    return [sum(frame[c::3]) / n for c in range(3)]


def pixel(frame, x, y):
    i = (y * SIZE[0] + x) * 3
    return tuple(frame[i:i + 3])


class TestHalation:
    def test_it_only_ever_adds_light_on_every_channel(self, env):
        """A screen cannot darken. Negotiated in YUV it did: mean green fell
        26/255, because the chroma planes were screened too."""
        _ffmpeg_or_skip()
        (before,) = frames("format=gbrp", source=BARS)
        (after,) = frames(_vf(env, Effect(name="halation")), source=BARS)
        darker = sum(1 for b, a in zip(before, after) if a < b - 1)
        assert darker == 0, f"{darker} channel samples got darker"
        assert after != before, "halation changed nothing"

    def test_the_default_tint_is_red_orange(self, env):
        _ffmpeg_or_skip()
        (before,) = frames("format=gbrp", source=BARS)
        (after,) = frames(_vf(env, Effect(name="halation")), source=BARS)
        gain = [a - b for a, b in zip(channel_means(after), channel_means(before))]
        assert gain[0] > gain[1] > 0 and gain[0] > gain[2] > 0, gain

    def test_a_threshold_above_every_pixel_changes_nothing(self, env):
        _ffmpeg_or_skip()
        (before,) = frames("format=gbrp")
        (after,) = frames(
            _vf(env, Effect(name="halation", params={"threshold": 1.0}))
        )
        assert max(abs(a - b) for a, b in zip(after, before)) <= 1

    def test_it_cannot_be_gated_to_a_span(self, env):
        with pytest.raises(SpanUnsupported):
            _vf(env, Effect(name="halation", at=Span(0.0, 1.0)))


class TestBranchLabels:
    """A branching step carries pad labels, and it carries the same ones every
    time. That is safe only because ffmpeg binds labels in parse order."""

    def test_two_halations_in_one_chain_equal_two_passes(self, env):
        _ffmpeg_or_skip()
        red = Effect(name="halation", params={"tint": (1, 0, 0), "threshold": 0.3})
        blue = Effect(name="halation", params={"tint": (0, 0, 1), "threshold": 0.3})
        both = _vf(env, red, blue)
        assert both.count("[lk_a]") == 4, both
        in_one = frames(both)
        in_two = frames(f"{_vf(env, red)},format=rgb24,{_vf(env, blue)}")
        assert in_one == in_two

    def test_a_plan_splices_between_host_filters(self, env):
        _ffmpeg_or_skip()
        frames(f"null,{_vf(env, Effect(name='halation'))},null")


class TestCurvesAndColorbalance:
    def test_curves_lifts_the_floor_and_lowers_the_ceiling(self, env):
        _ffmpeg_or_skip()
        fragment = _vf(env, Effect(name="curves", params={"all": [(0, 0.1), (1, 0.9)]}))
        (after,) = frames(fragment, source=BARS)
        assert min(after) >= 0.1 * 255 - 2 and max(after) <= 0.9 * 255 + 2

    def test_curves_is_always_pchip(self, env):
        fragment = _vf(env, Effect(name="curves", params={"red": [(0, 0), (1, 1)]}))
        assert fragment.endswith(":interp=pchip")

    def test_a_shadow_shift_moves_shadows_more_than_highlights(self, env):
        _ffmpeg_or_skip()
        (before,) = frames("format=gbrp", source=BARS)
        (after,) = frames(
            _vf(env, Effect(name="colorbalance", params={"shadows": (0, 0, 0.5)})),
            source=BARS,
        )
        dark = [i for i in range(0, len(before), 3) if sum(before[i:i + 3]) < 150]
        bright = [i for i in range(0, len(before), 3) if sum(before[i:i + 3]) > 600]
        assert dark and bright
        lift = lambda idx: sum(after[i + 2] - before[i + 2] for i in idx) / len(idx)  # noqa: E731
        assert lift(dark) > lift(bright) + 5, (lift(dark), lift(bright))


class TestVignette:
    def test_it_darkens_the_corners_and_not_the_centre(self, env):
        _ffmpeg_or_skip()
        flat = "color=c=0xC0C0C0:size=64x48:rate=10"
        (after,) = frames(_vf(env, Effect(name="vignette")), source=flat)
        centre, corner = pixel(after, 32, 24), pixel(after, 0, 0)
        assert all(c >= 0xC0 - 3 for c in centre), centre
        assert all(k < c - 20 for k, c in zip(corner, centre)), (corner, centre)


class TestGrain:
    def test_it_is_redrawn_every_frame(self, env):
        _ffmpeg_or_skip()
        flat = "color=c=gray:size=64x48:rate=10"
        first, second = frames(_vf(env, Effect(name="grain")), source=flat, count=2)
        assert first != second

    def test_a_seed_is_a_picture(self, env):
        _ffmpeg_or_skip()
        flat = "color=c=gray:size=64x48:rate=10"
        grain = lambda seed: _vf(env, Effect(name="grain", params={"seed": seed}))  # noqa: E731
        assert frames(grain(3), source=flat) == frames(grain(3), source=flat)
        assert frames(grain(3), source=flat) != frames(grain(4), source=flat)

    def test_there_is_no_static_switch(self, env):
        with pytest.raises(CompileError, match="temporal"):
            _vf(env, Effect(name="grain", params={"temporal": False}))

    def test_a_plan_with_grain_reads_the_clock(self, env):
        plan = compile_look(Look(steps=(Effect(name="grain"),)), clip=CLIP, env=env)
        assert plan.time_varying is True


class TestGateWeave:
    def test_the_frame_keeps_its_size_and_wanders(self, env):
        """`frames` asserts the byte count, so a size change fails there."""
        _ffmpeg_or_skip()
        fragment = _vf(env, Effect(name="gate_weave", params={"amplitude": 4}))
        out = frames(fragment, source="testsrc2=size=64x48:rate=10,loop=-1:1", count=4)
        assert len(set(out)) > 1, "a still picture did not wander"

    def test_it_reads_the_clock_and_cannot_be_gated(self, env):
        plan = compile_look(
            Look(steps=(Effect(name="gate_weave"),)), clip=CLIP, env=env
        )
        assert plan.time_varying is True
        with pytest.raises(SpanUnsupported):
            _vf(env, Effect(name="gate_weave", at=Span(0.0, 1.0)))


class TestGammaDirection:
    def test_gamma_above_one_brightens(self, env):
        """The `eq` convention, pinned because a survey agent assumed the
        opposite and wrote it into a plan (issue #25)."""
        _ffmpeg_or_skip()
        grey = "color=c=0x808080:size=64x48:rate=10"
        (after,) = frames(_vf(env, Effect(name="gamma", params={"gamma": 1.5})), source=grey)
        assert all(c > 0x80 + 20 for c in pixel(after, 0, 0))


@pytest.mark.parametrize(
    "effect, params",
    [
        ("curves", {"all": [(0, 0)]}),
        ("curves", {"all": [(0.5, 0), (0.2, 1)]}),
        ("curves", {"red": [(0, 0), (1, 1.5)]}),
        ("colorbalance", {"shadows": (0, 0, 2)}),
        ("colorbalance", {"midtones": (0, 0)}),
        ("vignette", {"angle": 0}),
        ("vignette", {"angle": 2.0}),
        ("halation", {"threshold": 1.5}),
        ("halation", {"sigma": 0}),
        ("halation", {"amount": 2}),
        ("halation", {"tint": (1, -1, 0)}),
        ("grain", {"strength": 101}),
        ("grain", {"seed": -1}),
        ("gate_weave", {"amplitude": -1}),
        ("gate_weave", {"frequency": (1,)}),
    ],
)
def test_a_parameter_no_implementation_could_honour_is_refused(env, effect, params):
    with pytest.raises(CompileError, match=effect):
        _vf(env, Effect(name=effect, params=params))


def test_curves_needs_points(env):
    from looks.ffmpeg import FfmpegBackendError

    with pytest.raises(FfmpegBackendError, match="needs points"):
        _vf(env, Effect(name="curves"))
