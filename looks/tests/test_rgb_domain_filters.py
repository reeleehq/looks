"""`RGB_DOMAIN_FILTERS` is pinned against the ffmpeg binary that runs the tests.

Rule 22's refusal is only as good as that list: a filter that converts YUV to
RGB around itself but is missing from it reads as safe and ships ffmpeg 6.1's
luma shift (issue #29). The list was first written from memory, and the review
of #35 found seven filters missing, read off ffmpeg's `auto_scale` debug lines.
These tests read the same lines, in both directions:

* every listed filter, run on a yuv420p source, must be auto-scaled to RGB
  (an entry that is not RGB-only is wrong);
* every filter of the binary that auto-scales to RGB with default arguments
  must be listed (an omission is the real drift). Filters that refuse default
  arguments cannot be swept and are a blind spot: ``UNSWEPT`` names the known
  ones.

A filter this binary lacks is skipped inside the body, so the absence shows in
the skip count.
"""

import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor

import pytest

from looks.environment import probe
from looks.ffmpeg import RGB_DOMAIN_FILTERS, is_rgb_domain

_CUBE_3D = "LUT_3D_SIZE 2\n" + "".join(
    f"{r} {g} {b}\n" for b in (0, 1) for g in (0, 1) for r in (0, 1)
)
_CUBE_1D = "LUT_1D_SIZE 2\n0 0 0\n1 1 1\n"

#: Filters whose default arguments are not a valid invocation, so they get an
#: explicit one. The rest of the list is run bare.
INVOCATIONS = {
    "lutrgb": "lutrgb=r=val",
    "colorchannelmixer": "colorchannelmixer=rr=1",
    "colorbalance": "colorbalance=rs=0",
    "colorlevels": "colorlevels=rimin=0",
    "curves": "curves=all='0/0 1/1'",
    "lut3d": "lut3d=file=id3.cube",
    "exposure": "exposure=exposure=0",
    "huesaturation": "huesaturation=hue=0",
    "vibrance": "vibrance=intensity=0",
    "colortemperature": "colortemperature=temperature=6500",
    "colorcontrast": "colorcontrast=rc=0",
    "selectivecolor": "selectivecolor=reds='0 0 0 0'",
    "lut1d": "lut1d=file=id1.cube",
    "tonemap": "tonemap=none",
}
#: Filters that work in YUV and so must stay off the list.
YUV_CAPABLE = {
    "lutyuv": "lutyuv=y=val",
    "gblur": "gblur=sigma=1",
    "unsharp": "unsharp",
    "hue": "hue=h=0",
}
#: V->V filters that refuse default arguments, so the sweep cannot see them.
#: `geq` is RGB only in its r=/g=/b= form; the other two work in YUV.
UNSWEPT = frozenset({"geq", "colorspace", "colormatrix"})

#: A handful of seconds each on a slow runner; the sweep runs them in a pool.
_PROCESS_TIMEOUT_S = 30
_SWEEP_WORKERS = 8
_SOURCE = "testsrc2=s=64x48:r=1:d=1,format=yuv420p"
_CONVERSION = re.compile(
    r"\[auto_scale_\d+ @ \w+\] w:\d+ h:\d+ fmt:(\w+) .*-> .*fmt:(\w+) "
)
_RGB_FORMAT = re.compile(r"^(0?rgb|0?bgr|gbr|a?rgb|abgr|rgba|bgra)")


@pytest.fixture(scope="module")
def env():
    e = probe()
    if not e.available or shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not usable")
    return e


@pytest.fixture(scope="module")
def cubes(tmp_path_factory):
    """A folder with two tiny identity LUTs; ffmpeg runs with it as cwd.

    Bare file names, not absolute paths: a Windows drive colon ends a filter
    option.
    """
    folder = tmp_path_factory.mktemp("cubes")
    (folder / "id3.cube").write_text(_CUBE_3D)
    (folder / "id1.cube").write_text(_CUBE_1D)
    return folder


def _run_filter(invocation, cwd):
    return subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-v", "debug",
            "-f", "lavfi", "-i", _SOURCE,
            "-vf", invocation,
            "-frames:v", "1", "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
        errors="replace",
        cwd=cwd,
        timeout=_PROCESS_TIMEOUT_S,
    )  # fmt: skip


def _converts_to_rgb(stderr) -> bool:
    """Whether ffmpeg auto-inserted a YUV -> RGB scaler (the `auto_scale` line)."""
    return any(
        src.startswith("yuv") and _RGB_FORMAT.match(dst)
        for src, dst in _CONVERSION.findall(stderr)
    )


def _require(env, name):
    if name not in env.filters:
        pytest.skip(f"this ffmpeg has no {name!r} filter")


@pytest.mark.parametrize("name", sorted(UNSWEPT))
def test_an_unswept_filter_really_refuses_defaults(env, cubes, name):
    """Else the blind spot is smaller than stated, and `UNSWEPT` has rotted."""
    _require(env, name)
    assert _run_filter(name, cubes).returncode != 0


@pytest.mark.parametrize("name", sorted(RGB_DOMAIN_FILTERS))
def test_a_listed_filter_is_auto_scaled_to_rgb(env, cubes, name):
    _require(env, name)
    result = _run_filter(INVOCATIONS.get(name, name), cubes)
    assert result.returncode == 0, f"{name}: {result.stderr[-400:]}"
    assert _converts_to_rgb(result.stderr), name


@pytest.mark.parametrize("name", sorted(YUV_CAPABLE))
def test_a_yuv_capable_filter_is_not_auto_scaled(env, cubes, name):
    _require(env, name)
    assert not is_rgb_domain((name,))
    result = _run_filter(YUV_CAPABLE[name], cubes)
    assert result.returncode == 0, f"{name}: {result.stderr[-400:]}"
    assert not _converts_to_rgb(result.stderr), name


def _video_filters() -> list[str]:
    listing = subprocess.run(
        ["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True
    ).stdout
    return re.findall(r"^ [.TSC|A-Z]{2,3} (\w+)\s+V->V ", listing, re.M)


def test_no_filter_of_this_binary_converts_to_rgb_unlisted(env, cubes):
    """The drift guard: sweep every V->V filter with default arguments."""

    def converts(name):
        try:
            result = _run_filter(name, cubes)
        except subprocess.TimeoutExpired:
            return False
        return result.returncode == 0 and _converts_to_rgb(result.stderr)

    names = _video_filters()
    assert len(names) > 100, "the filter listing did not parse"
    with ThreadPoolExecutor(_SWEEP_WORKERS) as pool:
        flags = list(pool.map(converts, names))
    unlisted = {n for n, hit in zip(names, flags) if hit} - RGB_DOMAIN_FILTERS
    assert not unlisted, (
        f"{sorted(unlisted)} auto-scale YUV to RGB but are not in "
        "RGB_DOMAIN_FILTERS: rule 22 would let them through (add them, "
        "with an invocation if their defaults are not valid)"
    )
