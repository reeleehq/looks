"""`YUV_DOMAIN_FILTERS` pinned against the binary, and its use on an RGB clip (issue #56).

The mirror of `test_rgb_domain_filters.py`. A filter that only takes YUV makes
ffmpeg convert an RGB input to YUV and back around itself, with a matrix
nothing declares, so a luma operation acts on BT.601 luma whatever the clip
says. These tests read ffmpeg's `auto_scale` debug lines in both directions:

* every listed filter, run on an rgb24 source, must be auto-scaled to YUV;
* every filter of the binary that auto-scales rgb24 to YUV with default
  arguments must be listed.

Then the point of the list: on an RGB clip that declares its colour space,
`vf` wraps a YUV-only step in the clip's matrix, and the pixels are those of
an explicit conversion with that matrix.

A filter this binary lacks is skipped inside the body, so the absence shows in
the skip count.
"""

import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pytest

from looks import ClipSpec, Effect, Look, compile_look, vf
from looks.environment import probe
from looks.ffmpeg import YUV_DOMAIN_FILTERS, is_rgb_pix_fmt, matrix_wrap

#: Filters whose default arguments are not a valid invocation.
INVOCATIONS = {
    "lutyuv": "lutyuv=y=val",
    "geq": "geq=lum=p(X\\,Y)",
    "ocr": None,  # needs tesseract data; listed from 6.1's sweep, not run here
}
#: Listed because one build converts around it and the other does not:
#: `showpalette` auto-scales rgb24 to YUV on 9.0.1, not on 6.1.6. The list is
#: the union, so on the other build it is only checked to run.
BUILD_DEPENDENT = frozenset({"showpalette"})
_PROCESS_TIMEOUT_S = 30
_SWEEP_WORKERS = 8
_SOURCE = "testsrc2=s=64x48:r=1:d=1,format=rgb24"
_CONVERSION = re.compile(
    r"\[auto_scale_\d+ @ \w+\] w:\d+ h:\d+ fmt:(\w+) .*-> .*fmt:(\w+) "
)


@pytest.fixture(scope="module")
def env():
    e = probe()
    if not e.available or shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not usable")
    return e


def _run(invocation, *, source=_SOURCE, out=("-f", "null", "-"), level="debug"):
    return subprocess.run(
        ["ffmpeg", "-hide_banner", "-v", level, "-f", "lavfi", "-i", source,
         "-vf", invocation, "-frames:v", "1", *out],
        capture_output=True, text=True, errors="replace", timeout=_PROCESS_TIMEOUT_S,
    )  # fmt: skip


def _converts_to_yuv(stderr) -> bool:
    """Whether ffmpeg auto-inserted an RGB -> YUV scaler."""
    return any(
        is_rgb_pix_fmt(src) and not is_rgb_pix_fmt(dst) and not dst.startswith("gray")
        for src, dst in _CONVERSION.findall(stderr)
    )


@pytest.mark.parametrize("name", sorted(YUV_DOMAIN_FILTERS))
def test_a_listed_filter_is_auto_scaled_to_yuv(env, name):
    if name not in env.filters:
        pytest.skip(f"this ffmpeg has no {name!r} filter")
    invocation = INVOCATIONS.get(name, name)
    if invocation is None:
        pytest.skip(f"{name!r} cannot run without external data")
    result = _run(invocation)
    assert result.returncode == 0, f"{name}: {result.stderr[-400:]}"
    if name not in BUILD_DEPENDENT:
        assert _converts_to_yuv(result.stderr), name


def _video_filters() -> list[str]:
    listing = subprocess.run(
        ["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True
    ).stdout
    return re.findall(r"^ [.TSC|A-Z]{2,3} (\w+)\s+V->V ", listing, re.M)


def test_no_filter_of_this_binary_converts_rgb_to_yuv_unlisted(env):
    """The drift guard: sweep every V->V filter with default arguments."""

    def converts(name):
        try:
            result = _run(name)
        except subprocess.TimeoutExpired:
            return False
        return result.returncode == 0 and _converts_to_yuv(result.stderr)

    names = _video_filters()
    assert len(names) > 100, "the filter listing did not parse"
    with ThreadPoolExecutor(_SWEEP_WORKERS) as pool:
        flags = list(pool.map(converts, names))
    unlisted = {n for n, hit in zip(names, flags) if hit} - YUV_DOMAIN_FILTERS
    assert not unlisted, (
        f"{sorted(unlisted)} auto-scale RGB to YUV but are not in "
        "YUV_DOMAIN_FILTERS: an RGB clip would reach them with ffmpeg's "
        "matrix (add them)"
    )


def _clip(color_space):
    return ClipSpec(
        width=64, height=48, fps=1, pix_fmt="rgb24", color_space=color_space
    )


def _rgb(chain, *, source=_SOURCE):
    out = ("-f", "rawvideo", "-pix_fmt", "rgb24", "-")
    result = subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", source, "-vf", chain,
         "-frames:v", "1", *out],
        capture_output=True, check=True,
    )  # fmt: skip
    return result.stdout


def _contrast(env, color_space):
    look = Look(steps=(Effect(name="contrast", params={"amount": 1.3}),))
    return vf(compile_look(look, clip=_clip(color_space), env=env))


def test_an_rgb_clip_s_yuv_step_runs_in_the_clip_s_matrix(env):
    """The wrapped chain gives the pixels of an explicit conversion in the
    declared matrix, and not those of ffmpeg's own guess."""
    chain = _contrast(env, "bt709")
    wrap = matrix_wrap(_clip("bt709"))
    assert chain.startswith(wrap) and chain.endswith(wrap), chain
    step = chain[len(wrap) + 1 : -len(wrap) - 1]
    explicit = (
        "scale=out_color_matrix=bt709:out_range=tv,format=yuv444p,"
        f"{step},scale=in_color_matrix=bt709:in_range=tv,format=rgb24"
    )
    guessed = _rgb(step)
    wrapped = _rgb(chain)
    assert wrapped == _rgb(explicit)
    assert wrapped != guessed, "the declared matrix changed nothing"


def test_the_matrix_declared_is_the_one_the_clip_says(env):
    assert _rgb(_contrast(env, "bt709")) != _rgb(_contrast(env, "bt601"))


def test_a_yuv_clip_chain_is_unchanged(env):
    """No wrap around a YUV-only step on a YUV clip: it was never converted."""
    clip = ClipSpec(width=64, height=48, fps=1, pix_fmt="yuv420p", color_space="bt709")
    look = Look(steps=(Effect(name="contrast", params={"amount": 1.3}),))
    assert "scale=" not in vf(compile_look(look, clip=clip, env=env))


def test_an_rgb_clip_s_rgb_step_keeps_its_wrap(env):
    """`curves` on an RGB clip stays wrapped: the wrap pins its depth (#33)."""
    look = Look(steps=(Effect(name="curves", params={"all": [(0, 0), (1, 1)]}),))
    chain = vf(compile_look(look, clip=_clip("bt709"), env=env))
    assert chain.startswith(matrix_wrap(_clip("bt709")))
