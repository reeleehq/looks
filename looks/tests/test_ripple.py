"""The ripple transition (issue #49): measured on decoded pixels, never assumed.

Offline and free: every source is a pinned ``lavfi`` pattern, every process ends
in rawvideo on a pipe or ``-f null -``.
"""

import cmath
import shutil
import subprocess

import pytest

from looks import ClipSpec, Effect, Look, Ripple, Transition, compile_look, vf
from looks.environment import probe
from looks.ffmpeg import FfmpegBackendError, _ripple_compiler
from looks.params import with_defaults
from looks.transition import TransitionError, xfade_options

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


def _chain(env, clip, *, offset=START, duration=DURATION, **ripple):
    effect = Ripple(duration, **ripple).effect(offset=offset)
    return vf(compile_look(Look(steps=(effect,)), clip=clip, env=env))


def _source(width, height, pix_fmt, *, planes=("lum",), pattern=PATTERN, frames=FRAMES):
    """The pattern in ``planes``, neutral elsewhere, converted to ``pix_fmt``."""
    exprs = {p: pattern for p in planes}
    exprs.setdefault("cb", "128")
    exprs.setdefault("cr", "128")
    base = "yuva444p" if "a" in planes else "yuv444p"
    options = ":".join(f"{k}='{v}'" for k, v in exprs.items())
    return (
        f"nullsrc=size={width}x{height}:rate={FPS}:duration={frames / FPS},"
        f"format={base},geq={options},format={pix_fmt}"
    )


def _flat(width, height, pix_fmt, luma, *, color_range=None):
    """A flat picture at ``luma`` (in ``pix_fmt``'s own codes), optionally tagged."""
    tag = f",setrange={color_range}" if color_range else ""
    neutral = 512 if "10" in pix_fmt else 128
    return (
        f"nullsrc=size={width}x{height}:rate={FPS}:duration={FRAMES / FPS},"
        f"format={pix_fmt},geq=lum={luma}:cb={neutral}:cr={neutral}{tag}"
    )


def _luma_codes(frame, width, height, *, bytes_per_sample=1):
    """The luma plane of one raw frame, as integer codes."""
    n = width * height * bytes_per_sample
    if bytes_per_sample == 1:
        return list(frame[:n])
    return [int.from_bytes(frame[i : i + 2], "little") for i in range(0, n, 2)]


def _mean(values):
    return sum(values) / len(values)


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


def test_a_document_is_coerced_as_json_brings_it_back():
    """Ints and a list, as JSON would return them."""
    r = Ripple.from_dict(
        {"kind": "ripple", "duration_s": 1, "wavelengths": [0.1, 0.05]}
    )
    assert r == Ripple(1.0, wavelengths=(0.1, 0.05))
    assert isinstance(r.duration_s, float) and isinstance(r.wavelengths, tuple)


def test_a_stored_ripple_and_a_stored_fade_are_never_confused():
    ripple = Ripple(1.0).to_dict()
    assert ripple["kind"] == "ripple"
    with pytest.raises(TransitionError, match="not a Transition document"):
        Transition.from_dict(ripple)
    with pytest.raises(TransitionError, match="not a Ripple document"):
        Ripple.from_dict(Transition(1.0).to_dict())
    with pytest.raises(TransitionError, match="not a Ripple document"):
        Ripple.from_dict({**ripple, "kind": "fade"})
    assert Transition.from_dict({"kind": "xfade", "duration_s": 1}) == Transition(1.0)


def test_the_effect_carries_no_kind():
    """The schema refuses an unknown key, so the record's kind must stay out."""
    params = Ripple(1.0).effect(offset=0).params
    assert "kind" not in params
    assert set(params) == {"start_s", "duration_s", "amplitude", "wavelengths", "bloom"}


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


@pytest.mark.parametrize("bloom", [0, Ripple(1).bloom])
def test_the_look_is_the_same_at_any_size(env, bloom):
    """Sizes are fractions of the frame: twice the pixels, the same picture.

    With the bloom on too, whose blur is sized from the clip at compile time.
    """
    small = _split(
        _frames(
            _source(160, 90, "yuv444p"),
            _chain(env, _clip(160, 90, "yuv444p"), bloom=bloom),
            out_pix_fmt="gray",
        ),
        FRAMES,
    )[PEAK]
    large_chain = (
        _chain(env, _clip(320, 180, "yuv444p"), bloom=bloom)
        + ",scale=160:90:flags=area"
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


def test_the_bloom_is_sized_by_the_height_not_the_width(env):
    """Same height, twice the width: the glow along a column must not change.

    Stripes vary along Y only and the warp is off, so a column sees only the
    blur's vertical extent. Proportional sizes cannot tell height from width;
    this aspect change can.
    """
    stripes = "128+90*cos(2*PI*4*Y/H)"

    def column(width, bloom):
        source = _source(width, 90, "yuv444p", pattern=stripes)
        chain = _chain(env, _clip(width, 90, "yuv444p"), amplitude=0, bloom=bloom)
        peak = _split(_frames(source, chain, out_pix_fmt="gray"), FRAMES)[PEAK]
        return [peak[y * width + width // 2] for y in range(90)]

    narrow, wide = column(160, Ripple(1).bloom), column(320, Ripple(1).bloom)
    assert _mean_abs(narrow, column(160, 0)) > 2, "no glow to compare"
    assert _mean_abs(narrow, wide) < 0.5


def test_the_motion_is_the_same_wherever_the_window_lands(env):
    """Phases count from the window's start: one record, one picture.

    Measured before the fix (phases in absolute ``T``): mean |diff| 13.7
    between the two peaks, against an effect of 15.5.
    """
    frames = 40
    source = _source(160, 90, "yuv420p", frames=frames)
    plain = _split(_frames(source, "", out_pix_fmt="gray"), frames)

    def peak(offset):
        chain = _chain(env, _clip(160, 90), offset=offset)
        k = round((offset + DURATION / 2) * FPS)
        return k, _split(_frames(source, chain, out_pix_fmt="gray"), frames)[k]

    (k1, early), (k2, late) = peak(1.0), peak(2.3)
    assert _mean_abs(early, plain[k1]) > 5, "the peak did not move"
    assert _mean_abs(early, late) < 0.5


def test_the_strongest_frame_is_the_dissolves_midpoint(env):
    """The warp peaks where ``xfade``, given the same window, is at 50%.

    Both measured: ``xfade``'s mix on two flat sources, and the ripple's mean
    displacement from the source. A short window at a frame-unaligned start,
    so the frames either side of the peak sit well below it (sin² of 0.75).
    """
    offset, duration = 1.2, 0.6
    ripple = Ripple(duration, bloom=0)
    lo, hi = 40, 200
    options = xfade_options(ripple.dissolve, offset=offset, fps=FPS)
    xfade = "xfade=" + ":".join(f"{k}={v}" for k, v in options.items())
    flat = [_flat(64, 36, "yuv420p", value) for value in (lo, hi)]
    argv = ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", flat[0], "-f", "lavfi"]
    argv += ["-i", flat[1], "-filter_complex", f"[0][1]{xfade},format=gray"]
    raw = subprocess.run(
        argv + ["-f", "rawvideo", "-"], capture_output=True, check=True
    )
    mixes = [
        (_mean(f) - lo) / (hi - lo)
        for f in _split(raw.stdout, len(raw.stdout) // (64 * 36))
    ]
    halfway = min(range(len(mixes)), key=lambda k: abs(mixes[k] - 0.5))
    assert abs(mixes[halfway] - 0.5) < 0.02

    source = _source(160, 90, "yuv420p")
    plain = _split(_frames(source, "", out_pix_fmt="gray"), FRAMES)
    rippled = _split(
        _frames(
            source,
            _chain(env, _clip(160, 90), offset=offset, duration=duration, bloom=0),
            out_pix_fmt="gray",
        ),
        FRAMES,
    )
    moved = [_mean_abs(a, b) for a, b in zip(rippled, plain)]
    assert max(range(FRAMES), key=moved.__getitem__) == halfway


def test_the_bloom_swells_to_the_peak_and_settles_symmetrically(env):
    """Per frame, the bloom's brightening follows the envelope: up, then down."""
    source = _source(160, 90, "yuv420p")
    plain = _split(
        _frames(source, _chain(env, _clip(160, 90), bloom=0), out_pix_fmt="gray"),
        FRAMES,
    )
    bloomed = _split(
        _frames(source, _chain(env, _clip(160, 90)), out_pix_fmt="gray"), FRAMES
    )
    window = range(int(START * FPS) + 1, round((START + DURATION) * FPS))
    lift = {k: _mean(bloomed[k]) - _mean(plain[k]) for k in window}
    rising = [lift[k] for k in window if k <= PEAK]
    falling = [lift[k] for k in window if k >= PEAK]
    assert all(a < b for a, b in zip(rising, rising[1:])), rising
    assert all(a > b for a, b in zip(falling, falling[1:])), falling
    for k in range(1, PEAK - window.start + 1):
        assert abs(lift[PEAK - k] - lift[PEAK + k]) < 0.5, (k, lift)


def test_the_bloom_lift_is_the_same_proportion_at_any_depth(env):
    """A flat mid-grey at 8 and 10 bits brightens by the same fraction of scale."""

    def lift(pix_fmt, luma, scale):
        chain = _chain(env, _clip(64, 36, pix_fmt), amplitude=0)
        raw = _frames(_flat(64, 36, pix_fmt, luma), chain, out_pix_fmt=pix_fmt)
        peak = _split(raw, FRAMES)[PEAK]
        codes = _luma_codes(peak, 64, 36, bytes_per_sample=scale)
        return (_mean(codes) - luma) / (255 if scale == 1 else 1023)

    eight, ten = lift("yuv420p", 128, 1), lift("yuv420p10le", 512, 2)
    assert eight > 10 / 255, "no bloom to compare"
    assert abs(eight - ten) < 1 / 255


@pytest.mark.parametrize(
    "color_range, luma, check",
    [
        # Full range: a highlight the bloom brightens must not come out darker.
        # Clipped at lutyuv's limited maxval it did: 250 became 241.
        ("pc", 250, lambda peak: peak > 250),
        # Limited, and untagged (which ffmpeg treats as limited): nominal white
        # stays nominal white; unclipped it would rise to 246.
        ("tv", 235, lambda peak: peak == 235),
        (None, 235, lambda peak: peak == 235),
    ],
)
def test_the_bloom_respects_the_clips_range(env, color_range, luma, check):
    clip = ClipSpec(
        width=64,
        height=36,
        fps=FPS,
        pix_fmt="yuv420p",
        color_space="bt709",
        color_range=color_range,
    )
    effect = Ripple(DURATION, amplitude=0).effect(offset=START)
    chain = vf(compile_look(Look(steps=(effect,)), clip=clip, env=env))
    source = _flat(64, 36, "yuv420p", luma, color_range=color_range)
    peak = _split(_frames(source, chain, out_pix_fmt="yuv420p"), FRAMES)[PEAK]
    mean = _mean(_luma_codes(peak, 64, 36))
    assert check(mean), mean


def _displacement_profiles(env, frames_wanted, *, width=256, height=400):
    """The horizontal displacement ``dx(Y)``, in pixels, read off a luma ramp.

    The source is ``4*X`` at 10 bits, so a bilinear read at ``X+dx`` returns
    ``4*(X+dx)`` exactly (to a quarter pixel), and a pattern constant in Y
    hides the vertical wander. Averaged over the middle columns, clear of any
    edge.
    """
    pix_fmt = "yuv420p10le"
    source = (
        f"nullsrc=size={width}x{height}:rate={FPS}:duration={FRAMES / FPS},"
        f"format=yuv444p10le,geq=lum=4*X:cb=512:cr=512,format={pix_fmt}"
    )
    # Whole cycles over the height (4 and 10), so the two harmonics are
    # orthogonal and a plain Fourier projection separates them.
    chain = _chain(
        env, _clip(width, height, pix_fmt), wavelengths=(1 / 4, 1 / 10), bloom=0
    )
    frames = _split(_frames(source, chain, out_pix_fmt=pix_fmt), FRAMES)
    columns = range(width * 3 // 8, width * 5 // 8)
    profiles = {}
    for k in frames_wanted:
        codes = _luma_codes(frames[k], width, height, bytes_per_sample=2)
        profiles[k] = [
            _mean([codes[y * width + x] / 4 - x for x in columns])
            for y in range(height)
        ]
    return profiles


def _harmonic(profile, cycles):
    """The amplitude of ``profile``'s component at ``cycles`` per length."""
    n = len(profile)
    c = sum(
        v * cmath.exp(-2j * cmath.pi * cycles * y / n) for y, v in enumerate(profile)
    )
    return 2 * abs(c) / n


def test_the_displacement_has_both_harmonics_at_their_sizes(env):
    """At the peak, ``dx(Y)`` is the amplitude at the first wavelength and
    ``RIPPLE_HARMONIC`` of it at the second: measured, not read off the string."""
    from looks.ffmpeg import RIPPLE_HARMONIC

    width = 256
    profile = _displacement_profiles(env, [PEAK], width=width)[PEAK]
    expected = Ripple(1).amplitude * width
    assert abs(_harmonic(profile, 4) - expected) < 0.25
    assert abs(_harmonic(profile, 10) - RIPPLE_HARMONIC * expected) < 0.25


def test_the_ripple_moves_rather_than_breathes(env):
    """Two frames at the same envelope value, either side of the peak, differ:
    the phases advance with time, so the pattern travels."""
    before, after = PEAK - 1, PEAK + 1
    profiles = _displacement_profiles(env, [before, after])
    assert _mean_abs(profiles[before], profiles[after]) > 0.5


@pytest.mark.parametrize(
    "doc, match",
    [
        ({"kind": "ripple", "duration_s": 1, "amplitde": 0.02}, "amplitde"),
        ({"kind": "ripple", "duration_s": 1, "wavelengths": "ab"}, "not a Ripple"),
        ({"kind": "ripple", "duration_s": "one"}, "not a Ripple"),
    ],
)
def test_a_document_that_would_render_something_else_is_refused(doc, match):
    with pytest.raises(TransitionError, match=match):
        Ripple.from_dict(doc)


def test_the_bloom_leaves_chroma_where_it_was(env):
    """`lutyuv`'s default u/v clamp chroma to 16..240 (#63). A flat chroma of 4
    blooms to 4; clamped, the peak mixed it toward 16 (0.45*4 + 0.55*16)."""
    source = (
        f"nullsrc=size=160x90:rate={FPS}:duration={FRAMES / FPS},"
        "format=yuv444p,geq=lum=128:cb=4:cr=250"
    )
    chain = _chain(env, _clip(160, 90, "yuv444p"))
    peak = _split(_frames(source, chain, out_pix_fmt="yuv444p"), FRAMES)[PEAK]
    plane = 160 * 90
    u, v = peak[plane : 2 * plane], peak[2 * plane :]
    assert max(abs(c - 4) for c in u) <= 1 and max(abs(c - 250) for c in v) <= 1
