"""The ripple transition (issue #49): measured on decoded pixels, never assumed.

Offline and free: every source is a pinned ``lavfi`` pattern, every process ends
in rawvideo on a pipe or ``-f null -``.
"""

import shutil
import subprocess

import pytest

from looks import ClipSpec, Effect, Look, Ripple, Transition, compile_look, vf
from looks.environment import probe
from looks.ffmpeg import FfmpegBackendError, _ripple_compiler
from looks.params import with_defaults
from looks.transition import TransitionError

FPS = 10
#: The window: frames 10..20 at 10 fps, peaking at frame 15.
START, DURATION = 1.0, 1.0
PEAK = 15
FRAMES = 30
#: A smooth pattern, in normalised coordinates so it is the same picture at
#: any size. Written into luma, and into the planes asked to carry it too.
PATTERN = "128+90*sin(2*PI*5*X/W)*cos(2*PI*3*Y/H)"


def _ffmpeg_or_skip():
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not on PATH")


@pytest.fixture(scope="module")
def env():
    _ffmpeg_or_skip()
    e = probe()
    if not e.available:
        pytest.skip("ffmpeg not usable")
    return e


def _clip(width, height, pix_fmt="yuv420p"):
    return ClipSpec(
        width=width, height=height, fps=FPS, pix_fmt=pix_fmt, color_space="bt709"
    )


def _chain(env, clip, **ripple):
    effect = Ripple(DURATION, **ripple).effect(offset=START)
    return vf(compile_look(Look(steps=(effect,)), clip=clip, env=env))


def _source(width, height, pix_fmt, *, planes=("lum",)):
    """The pattern in ``planes``, neutral elsewhere, converted to ``pix_fmt``."""
    exprs = {p: PATTERN for p in planes}
    exprs.setdefault("cb", "128")
    exprs.setdefault("cr", "128")
    base = "yuva444p" if "a" in planes else "yuv444p"
    options = ":".join(f"{k}='{v}'" for k, v in exprs.items())
    return (
        f"nullsrc=size={width}x{height}:rate={FPS}:duration={FRAMES / FPS},"
        f"format={base},geq={options},format={pix_fmt}"
    )


def _frames(source, chain, *, out_pix_fmt):
    """Every frame, as raw bytes in ``out_pix_fmt``."""
    vf_arg = f"{chain},format={out_pix_fmt}" if chain else f"format={out_pix_fmt}"
    argv = ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", source, "-vf", vf_arg]
    argv += ["-f", "rawvideo", "-"]
    return subprocess.run(argv, capture_output=True, check=True).stdout


def _split(raw, count):
    size = len(raw) // count
    return [raw[i * size : (i + 1) * size] for i in range(count)]


def _mean_abs(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


# ------------------------------------------------------------------ the record


def test_the_dissolve_is_an_ordinary_cross_fade_of_the_same_length():
    assert Ripple(0.8).dissolve == Transition(0.8, "fade")


def test_the_effect_starts_where_the_dissolve_does():
    params = Ripple(0.8).effect(offset=6.3).params
    assert (params["start_s"], params["duration_s"]) == (6.3, 0.8)


@pytest.mark.parametrize(
    "kwargs, match",
    [
        ({"duration_s": 0}, "positive duration"),
        ({"duration_s": 1, "bloom": 1.5}, "bloom"),
        ({"duration_s": 1, "amplitude": -0.01}, "amplitude"),
        ({"duration_s": 1, "wavelengths": (0.1, 0)}, "wavelengths"),
        ({"duration_s": 1, "wavelengths": (0.1,)}, "wavelengths"),
    ],
)
def test_a_ripple_that_cannot_be_rendered_is_refused_at_construction(kwargs, match):
    with pytest.raises(TransitionError, match=match):
        Ripple(**kwargs)


def test_a_round_trip_through_a_document_keeps_the_record():
    r = Ripple(0.7, amplitude=0.02, wavelengths=[0.1, 0.05], bloom=0.3)
    assert Ripple.from_dict(r.to_dict()) == r
    assert r.wavelengths == (0.1, 0.05)


def test_the_bloom_needs_the_clip_and_no_bloom_does_not():
    params = with_defaults("ripple", {"start_s": 0, "duration_s": 1})
    with pytest.raises(FfmpegBackendError, match="ClipSpec"):
        _ripple_compiler(params)
    assert _ripple_compiler({**params, "bloom": 0})["filter"].startswith("geq=")


def test_a_span_on_the_effect_is_refused_at_selection(env):
    """It gates itself; an ``at`` would put ``enable`` on ``split``."""
    from looks.spec import Span, SpanUnsupported

    effect = Effect(
        name="ripple",
        params={"start_s": START, "duration_s": DURATION},
        at=Span(START, START + DURATION),
    )
    with pytest.raises(SpanUnsupported):
        compile_look(Look(steps=(effect,)), clip=_clip(64, 36), env=env)


# -------------------------------------------------------------------- the pixels


@pytest.mark.parametrize(
    "pix_fmt, out", [("yuv420p", "yuv420p"), ("yuv420p10le", "yuv420p10le")]
)
def test_outside_the_window_every_pixel_is_the_source(env, pix_fmt, out):
    source = _source(160, 90, pix_fmt)
    before = _split(_frames(source, "", out_pix_fmt=out), FRAMES)
    after = _split(
        _frames(source, _chain(env, _clip(160, 90, pix_fmt)), out_pix_fmt=out),
        FRAMES,
    )
    outside = [
        n for n in range(FRAMES) if not START * FPS < n < (START + DURATION) * FPS
    ]
    assert [n for n in outside if after[n] != before[n]] == []
    assert _mean_abs(after[PEAK], before[PEAK]) > 5, "the peak frame did not move"


def test_chroma_moves_exactly_with_luma(env):
    """The fault this replaces: ``displace`` with gray maps moved luma only.

    At 4:4:4, a source whose chroma plane IS its luma plane must stay that way.
    """
    source = _source(160, 90, "yuv444p", planes=("lum", "cb"))
    chain = _chain(env, _clip(160, 90, "yuv444p"), bloom=0)
    frames = _split(_frames(source, chain, out_pix_fmt="yuv444p"), FRAMES)
    plane = 160 * 90
    peak = frames[PEAK]
    luma, chroma = peak[:plane], peak[plane : 2 * plane]
    original = _split(_frames(source, "", out_pix_fmt="yuv444p"), FRAMES)[PEAK]
    assert _mean_abs(luma, original[:plane]) > 5, "the picture did not move"
    assert luma == chroma


@pytest.mark.parametrize("pix_fmt, sx, sy", [("yuv420p", 2, 2), ("yuv422p", 2, 1)])
def test_subsampled_chroma_follows_luma(env, pix_fmt, sx, sy):
    """A subsampled chroma plane must move as far, in its own pixels, as luma.

    Read against the luma plane sampled at the chroma grid: before the ripple
    the two agree to within the subsampling error, and they must still agree
    after it. Chroma left in place (the ``displace`` fault) disagrees by far
    more, and 4:2:2 catches a vertical wander scaled by the wrong axis.
    """
    width, height = 320, 180
    cw, ch = width // sx, height // sy
    source = _source(width, height, pix_fmt, planes=("lum", "cb"))
    chain = _chain(env, _clip(width, height, pix_fmt), bloom=0)

    def disagreement(frame):
        luma = frame[: width * height]
        chroma = frame[width * height : width * height + cw * ch]
        sampled = bytes(
            luma[(sy * y) * width + sx * x] for y in range(ch) for x in range(cw)
        )
        return _mean_abs(sampled, chroma)

    original = _split(_frames(source, "", out_pix_fmt=pix_fmt), FRAMES)[PEAK]
    rippled = _split(_frames(source, chain, out_pix_fmt=pix_fmt), FRAMES)[PEAK]
    luma_moved = _mean_abs(rippled[: width * height], original[: width * height])
    assert luma_moved > 5
    assert disagreement(rippled) < disagreement(original) + 2
    # The fault, for scale: chroma left where it was.
    stale = rippled[: width * height] + original[width * height :]
    assert disagreement(stale) > disagreement(rippled) + 5


def test_alpha_moves_with_the_picture_and_is_kept(env):
    source = _source(160, 90, "yuva444p", planes=("lum", "a"))
    chain = _chain(env, _clip(160, 90, "yuva444p"), bloom=0)
    peak = _split(_frames(source, chain, out_pix_fmt="yuva444p"), FRAMES)[PEAK]
    plane = 160 * 90
    assert peak[:plane] == peak[3 * plane :]


def test_ten_bits_stay_ten_bits(env):
    """``displace`` is 8-bit only; the warp must not cost the stream its depth."""
    source = (
        f"nullsrc=size=1024x2:rate={FPS}:duration={FRAMES / FPS},"
        "format=yuv444p10le,geq=lum=X:cb=512:cr=512,format=yuv420p10le"
    )
    chain = _chain(env, _clip(1024, 2, "yuv420p10le"))
    peak = _split(_frames(source, chain, out_pix_fmt="yuv420p10le"), FRAMES)[PEAK]
    luma = peak[: 1024 * 2 * 2]
    codes = {int.from_bytes(luma[i : i + 2], "little") for i in range(0, len(luma), 2)}
    assert len(codes) > 256


def test_the_look_is_the_same_at_any_size(env):
    """Sizes are fractions of the frame: twice the pixels, the same picture."""
    small = _split(
        _frames(
            _source(160, 90, "yuv444p"),
            _chain(env, _clip(160, 90, "yuv444p"), bloom=0),
            out_pix_fmt="gray",
        ),
        FRAMES,
    )[PEAK]
    large_chain = (
        _chain(env, _clip(320, 180, "yuv444p"), bloom=0) + ",scale=160:90:flags=area"
    )
    large = _split(
        _frames(_source(320, 180, "yuv444p"), large_chain, out_pix_fmt="gray"), FRAMES
    )[PEAK]
    unrippled = _split(
        _frames(_source(160, 90, "yuv444p"), "", out_pix_fmt="gray"), FRAMES
    )[PEAK]
    effect = _mean_abs(small, unrippled)
    assert effect > 5
    assert _mean_abs(small, large) < effect / 3


def test_the_bloom_brightens_at_the_peak_and_nowhere_else(env):
    source = _source(160, 90, "yuv420p")
    plane = 160 * 90
    plain = _split(
        _frames(source, _chain(env, _clip(160, 90), bloom=0), out_pix_fmt="yuv420p"),
        FRAMES,
    )
    bloomed = _split(
        _frames(source, _chain(env, _clip(160, 90)), out_pix_fmt="yuv420p"), FRAMES
    )

    def mean(frame):
        return sum(frame[:plane]) / plane

    assert mean(bloomed[PEAK]) > mean(plain[PEAK]) + 2
    assert bloomed[5] == plain[5] and bloomed[25] == plain[25]


def test_the_bloom_glows_in_colour_but_never_softens_alpha(env):
    source = _source(160, 90, "yuva444p", planes=("lum", "cb", "a"))
    clip = _clip(160, 90, "yuva444p")
    plane = 160 * 90
    plain = _split(
        _frames(source, _chain(env, clip, bloom=0), out_pix_fmt="yuva444p"), FRAMES
    )[PEAK]
    bloomed = _split(
        _frames(source, _chain(env, clip), out_pix_fmt="yuva444p"), FRAMES
    )[PEAK]
    assert bloomed[3 * plane :] == plain[3 * plane :], "the glow blurred the alpha"
    assert _mean_abs(bloomed[plane : 2 * plane], plain[plane : 2 * plane]) > 1, (
        "no chroma glow"
    )


def test_the_vertical_wander_is_scaled_per_plane_at_4_2_2(env):
    """Horizontal stripes see only the vertical wander, so at 4:2:2 (chroma at
    full height, half width) chroma must move exactly as far as luma. Scaled by
    the width ratio instead of the height ratio, it moves half as far."""
    width, height = 320, 180
    stripes = "128+90*cos(2*PI*4*Y/H)"
    source = (
        f"nullsrc=size={width}x{height}:rate={FPS}:duration={FRAMES / FPS},"
        f"format=yuv444p,geq=lum='{stripes}':cb='{stripes}':cr=128,format=yuv422p"
    )
    chain = _chain(env, _clip(width, height, "yuv422p"), amplitude=0.1, bloom=0)
    peak = _split(_frames(source, chain, out_pix_fmt="yuv422p"), FRAMES)[PEAK]
    original = _split(_frames(source, "", out_pix_fmt="yuv422p"), FRAMES)[PEAK]
    luma, chroma = (
        peak[: width * height],
        peak[width * height : width * height * 3 // 2],
    )
    sampled = bytes(
        luma[y * width + 2 * x] for y in range(height) for x in range(width // 2)
    )
    assert _mean_abs(luma, original[: width * height]) > 5, "the stripes did not move"
    assert _mean_abs(sampled, chroma) < 2
