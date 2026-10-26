"""The film effects of issue #25, checked on decoded pixels.

`test_ffmpeg.py` already sweeps every effect through the binary and
`test_time_varying.py` measures each one's clock-reading against its
declaration. This file asserts what each effect does to a **colour** picture,
on every channel (rule 29b's lesson: a grey ramp hides a per-channel bug), plus
the two mechanisms the effects brought with them — fixed pad labels inside a
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
#: The baseline for a step that works in RGB: the same conversion halation
#: makes, so a comparison measures the effect and not the conversion (an 8-bit
#: `gbrp` path differs from the 16-bit one by up to 117/255 on testsrc2).
RGB = "format=gbrp16le"


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
        (before,) = frames(RGB, source=BARS)
        (after,) = frames(_vf(env, Effect(name="halation")), source=BARS)
        darker = sum(1 for b, a in zip(before, after) if a < b - 1)
        assert darker == 0, f"{darker} channel samples got darker"
        assert after != before, "halation changed nothing"

    def test_the_default_tint_is_red_orange(self, env):
        _ffmpeg_or_skip()
        (before,) = frames(RGB, source=BARS)
        (after,) = frames(_vf(env, Effect(name="halation")), source=BARS)
        gain = [a - b for a, b in zip(channel_means(after), channel_means(before))]
        assert gain[0] > gain[1] > 0 and gain[0] > gain[2] > 0, gain

    def test_a_threshold_above_every_pixel_changes_nothing(self, env):
        _ffmpeg_or_skip()
        (before,) = frames(RGB)
        (after,) = frames(
            _vf(env, Effect(name="halation", params={"threshold": 1.0}))
        )
        assert max(abs(a - b) for a, b in zip(after, before)) <= 1

    def test_it_cannot_be_gated_to_a_span(self, env):
        with pytest.raises(SpanUnsupported):
            _vf(env, Effect(name="halation", at=Span(0.0, 1.0)))

    def _gain(self, env, **params):
        (before,) = frames(RGB, source=BARS)
        (after,) = frames(_vf(env, Effect(name="halation", params=params)), source=BARS)
        return [a - b for a, b in zip(channel_means(after), channel_means(before))]

    def test_amount_scales_the_glow(self, env):
        _ffmpeg_or_skip()
        assert max(abs(g) for g in self._gain(env, amount=0)) < 0.5
        assert self._gain(env, amount=1)[0] > self._gain(env, amount=0.5)[0] + 1

    def test_sigma_spreads_the_glow(self, env):
        """A wider blur reaches more pixels around each highlight."""
        _ffmpeg_or_skip()
        (before,) = frames(RGB, source=BARS)

        def reached(sigma):
            (after,) = frames(
                _vf(env, Effect(name="halation", params={"sigma": sigma})), source=BARS
            )
            return sum(1 for a, b in zip(after, before) if a > b + 1)

        assert reached(12) > reached(1)

    @pytest.mark.parametrize("lit", [0, 1, 2])
    def test_the_tint_says_which_channel_glows(self, env, lit):
        _ffmpeg_or_skip()
        tint = tuple(1.0 if c == lit else 0.0 for c in range(3))
        gain = self._gain(env, tint=tint)
        assert gain[lit] > 1
        assert all(abs(g) < 0.5 for c, g in enumerate(gain) if c != lit), gain


class TestBranchLabels:
    """A branching step carries pad labels, and it carries the same ones every
    time. That is safe only because ffmpeg binds labels in parse order."""

    def test_two_halations_in_one_chain_equal_two_passes(self, env):
        _ffmpeg_or_skip()
        red = Effect(name="halation", params={"tint": (1, 0, 0), "threshold": 0.3})
        blue = Effect(name="halation", params={"tint": (0, 0, 1), "threshold": 0.3})
        both = _vf(env, red, blue)
        assert both.count("[lk_a]") == 4, both
        # The same chain with the second step's labels renamed apart: if reuse
        # rewired anything, the pictures would differ.
        first = _vf(env, red)
        apart = first + "," + _vf(env, blue).replace("[lk_", "[other_")
        assert frames(both) == frames(apart)

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
        (before,) = frames(RGB, source=BARS)
        (after,) = frames(
            _vf(env, Effect(name="colorbalance", params={"shadows": (0, 0, 0.5)})),
            source=BARS,
        )
        dark = [i for i in range(0, len(before), 3) if sum(before[i:i + 3]) < 150]
        bright = [i for i in range(0, len(before), 3) if sum(before[i:i + 3]) > 600]
        assert dark and bright
        lift = lambda idx: sum(after[i + 2] - before[i + 2] for i in idx) / len(idx)  # noqa: E731
        assert lift(dark) > lift(bright) + 5, (lift(dark), lift(bright))


    def test_preserve_lightness_changes_the_picture(self, env):
        _ffmpeg_or_skip()
        shift = {"midtones": (0.4, 0, -0.4)}
        plain = frames(_vf(env, Effect(name="colorbalance", params=shift)), source=BARS)
        kept = frames(
            _vf(env, Effect(name="colorbalance",
                            params={**shift, "preserve_lightness": True})),
            source=BARS,
        )
        assert plain != kept


class TestVignette:
    def test_it_darkens_the_corners_and_not_the_centre(self, env):
        _ffmpeg_or_skip()
        flat = "color=c=0xC0C0C0:size=64x48:rate=10"
        (after,) = frames(_vf(env, Effect(name="vignette")), source=flat)
        centre, corner = pixel(after, 32, 24), pixel(after, 0, 0)
        assert all(c >= 0xC0 - 3 for c in centre), centre
        assert all(k < c - 20 for k, c in zip(corner, centre)), (corner, centre)

    def test_a_wider_angle_darkens_the_corners_more(self, env):
        _ffmpeg_or_skip()
        flat = "color=c=0xC0C0C0:size=64x48:rate=10"

        def corner(angle):
            (out,) = frames(
                _vf(env, Effect(name="vignette", params={"angle": angle})), source=flat
            )
            return sum(pixel(out, 0, 0))

        assert corner(1.2) < corner(0.4) - 20


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

    def test_one_seed_restarts_the_same_noise_at_every_cut(self, env):
        """The behaviour issue #30 documents: two parts rendered with one seed
        get the same grain, so the host passes a seed per part."""
        _ffmpeg_or_skip()
        flat = "color=c=gray:size=64x48:rate=10"
        grain = _vf(env, Effect(name="grain", params={"seed": 5}))
        # Part B starts 3 frames later in the same source, timestamps kept: if
        # the noise followed them it would differ from part A's.
        part_b = f"trim=start_frame=3,{grain}"
        assert frames(grain, source=flat, count=3) == frames(
            part_b, source=flat, count=3
        )

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

    @pytest.mark.parametrize(
        "source, size, sar, expected",
        [
            ("testsrc2=size=1920x1080", "1920x1080", "1", "1/1"),
            ("testsrc2=size=720x480", "720x480", "8/9", "8/9"),
            # A term above setsar's default max=100, which rounded to 67/46.
            ("testsrc2=size=720x576", "720x576", "118/81", "118/81"),
            # Unknown: made square, not left for the inverse to make 99/100.
            ("testsrc2=size=1280x720", "1280x720", "0/1", "1/1"),
            # An odd 4:2:0 frame. Through yuv444p, because a lavfi source
            # rounds an odd size when asked for 4:2:0 directly.
            ("color=c=gray:size=65x49", "65x49", "1", "1/1"),
        ],
    )
    def test_it_keeps_the_frame_size_and_aspect(self, env, source, size, sar, expected):
        """Read through `showinfo`: raw frames carry no aspect ratio, which is
        how a SAR of 4311:4304 — refused by a concat — first got past."""
        _ffmpeg_or_skip()
        source = f"{source}:rate=10,format=yuv444p,format=yuv420p,setsar={sar}:max=1000"

        def shown(fragment):
            proc = subprocess.run(
                ["ffmpeg", "-v", "info", "-f", "lavfi", "-i", source,
                 "-vf", f"{fragment},showinfo", "-frames:v", "3",
                 "-f", "null", "-"],
                capture_output=True, text=True,
            )
            assert proc.returncode == 0, proc.stderr[-600:]
            return [line for line in proc.stderr.splitlines() if " n:" in line]

        assert f"s:{size} " in shown("null")[0], "the test source is not that size"
        assert f"sar:{sar if '/' in sar else sar + '/1'} " in shown("null")[0]
        lines = shown(_vf(env, Effect(name="gate_weave", params={"amplitude": 6})))
        assert lines
        for line in lines:
            assert f"s:{size} " in line and f"sar:{expected} " in line, line

    def test_it_moves_by_single_pixels_on_420(self, env):
        """Without `exact=1`, crop snaps to the chroma grid: at amplitude 1, 48
        frames visit 4 positions instead of 9."""
        _ffmpeg_or_skip()
        fragment = _vf(env, Effect(name="gate_weave", params={"amplitude": 1}))
        out = frames(
            fragment,
            source="testsrc2=size=64x48:rate=10,format=yuv444p,loop=-1:1,format=yuv420p",
            count=48,
        )
        assert len(set(out)) > 6, len(set(out))

    def test_an_amplitude_bigger_than_the_frame_is_refused(self, env):
        from looks.ffmpeg import FfmpegBackendError

        with pytest.raises(FfmpegBackendError, match="amplitude"):
            _vf(env, Effect(name="gate_weave", params={"amplitude": 24}))

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
        ("colorbalance", {"preserve_lightness": "false"}),
        # Checked as EMITTED (six decimals): two x-points that collapse into
        # one, which `curves` refuses; an angle written as `angle=0`; a sigma
        # written as `sigma=0`.
        ("curves", {"all": [(0, 0), (0.5, 0.4), (0.5000001, 0.6), (1, 1)]}),
        ("vignette", {"angle": 1e-9}),
        ("halation", {"sigma": 1e-9}),
        # Past what the filter accepts.
        ("halation", {"sigma": 1025}),
        ("grain", {"seed": 2**31}),
        # Would be silently coerced: 7.9 -> 7, True -> 1, 2.9 -> 2, -0.5 -> 0.
        ("grain", {"strength": 7.9}),
        ("grain", {"strength": True}),
        ("grain", {"strength": "8"}),
        ("gate_weave", {"amplitude": 2.9}),
        ("gate_weave", {"amplitude": -0.5}),
        # A string is a sequence: "12" would read as the frequencies (1, 2).
        ("gate_weave", {"frequency": "12"}),
        ("halation", {"tint": "rgb"}),
        ("colorbalance", {"shadows": "abc"}),
        ("curves", {"all": "0/0 1/1"}),
        ("curves", {"all": [(0, 0), "11"]}),
        # A wrong type reaches the caller as a CompileError, not a bare
        # TypeError / ValueError from inside a check.
        ("halation", {"threshold": None}),
        ("vignette", {"angle": "wide"}),
        ("colorbalance", {"midtones": (0, 0, "x")}),
    ],
)
def test_a_parameter_no_implementation_could_honour_is_refused(env, effect, params):
    with pytest.raises(CompileError, match=effect):
        _vf(env, Effect(name=effect, params=params))


def test_an_integer_valued_float_is_accepted_as_that_integer(env):
    """Accepted, deliberately: ``8.0`` is emitted as ``8``, the picture asked for.

    Refusing it would refuse a value neither ffmpeg nor the compiler mishandles.
    """
    for effect, key, value in [
        ("grain", "strength", 8),
        ("grain", "seed", 3),
        ("gate_weave", "amplitude", 2),
    ]:
        as_float = _vf(env, Effect(name=effect, params={key: float(value)}))
        assert as_float == _vf(env, Effect(name=effect, params={key: value}))


def test_the_sigma_bound_is_gblurs(env):
    _ffmpeg_or_skip()
    halation = Effect(name="halation", params={"sigma": 1024})
    assert len(frames(_vf(env, halation))) == 1


#: Every parameter of every film effect, given explicitly and validly. A check
#: that crashed on every input would be wrapped into a CompileError and still
#: satisfy the refusal tests above; this is the test it would fail.
EVERY_PARAM = {
    "curves": {"all": [(0, 0.03), (1, 0.95)], "red": [(0, 0), (1, 1)],
               "green": [(0, 0), (1, 1)], "blue": [(0, 0), (1, 1)]},
    "colorbalance": {"shadows": (-0.03, 0, 0.04), "midtones": (0, 0, 0),
                     "highlights": (0.04, 0, -0.04), "preserve_lightness": True},
    "vignette": {"angle": 0.7},
    "halation": {"threshold": 0.7, "sigma": 8, "amount": 0.4, "tint": (1, 0.3, 0.2)},
    "grain": {"strength": 7, "seed": 7},
    "gate_weave": {"amplitude": 3, "frequency": (2.5, 1.5)},
}


@pytest.mark.parametrize("effect", sorted(EVERY_PARAM))
def test_every_parameter_given_validly_compiles_and_runs(env, effect):
    fragment = _vf(env, Effect(name=effect, params=EVERY_PARAM[effect]))
    _ffmpeg_or_skip()
    frames(fragment)


def test_halation_keeps_ten_bits(env):
    """Rule 23: an 8-bit `gbrp` kept 256 of 1024 codes on a 10-bit ramp."""
    _ffmpeg_or_skip()
    identity = _vf(env, Effect(name="halation", params={"threshold": 1.0}))
    proc = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi",
         "-i", "nullsrc=size=1024x2:rate=10,format=yuv444p10le,geq=lum=X:cb=512:cr=512",
         "-vf", f"{identity},format=gbrp16le", "-frames:v", "1",
         "-f", "rawvideo", "-pix_fmt", "gbrp16le", "-"],
        capture_output=True,
    )
    assert proc.returncode == 0, proc.stderr[-600:]
    plane = proc.stdout[: 1024 * 2 * 2]
    codes = {int.from_bytes(plane[i:i + 2], "little") for i in range(0, len(plane), 2)}
    assert len(codes) > 512, len(codes)


def test_curves_needs_points(env):
    from looks.ffmpeg import FfmpegBackendError

    with pytest.raises(FfmpegBackendError, match="needs points"):
        _vf(env, Effect(name="curves"))
