"""`RGB_DOMAIN_FILTERS` is pinned against the ffmpeg binary that runs the tests.

Rule 22's refusal is only as good as that list: a filter that converts YUV to
RGB around itself but is missing from it reads as safe and ships ffmpeg 6.1's
luma shift (issue #29). The list was first written from memory, and the review
of #35 found seven filters missing, read off ffmpeg's `auto_scale` debug lines.
This test reads the same lines, so the list cannot drift from the binary again.

Every listed filter is run once on a yuv420p source and must be auto-scaled to
an RGB format; a few YUV-capable filters must *not* be. Skipped per filter
(inside the body, so the absence is visible) when the binary lacks it.
"""

import re
import shutil
import subprocess

import pytest

from looks.environment import probe
from looks.ffmpeg import RGB_DOMAIN_FILTERS, is_rgb_domain

_CUBE_3D = "LUT_3D_SIZE 2\n" + "".join(
    f"{r} {g} {b}\n" for b in (0, 1) for g in (0, 1) for r in (0, 1)
)
_CUBE_1D = "LUT_1D_SIZE 2\n0 0 0\n1 1 1\n"

#: A minimal, valid argument string for each listed filter; `{cube3}` and
#: `{cube1}` are substituted with the paths of tiny identity LUT files.
INVOCATIONS = {
    "lutrgb": "lutrgb=r=val",
    "colorchannelmixer": "colorchannelmixer=rr=1",
    "colorbalance": "colorbalance=rs=0",
    "colorlevels": "colorlevels=rimin=0",
    "curves": "curves=all='0/0 1/1'",
    "lut3d": "lut3d=file={cube3}",
    "exposure": "exposure=exposure=0",
    "huesaturation": "huesaturation=hue=0",
    "vibrance": "vibrance=intensity=0",
    "colortemperature": "colortemperature=temperature=6500",
    "colorcontrast": "colorcontrast=rc=0",
    "selectivecolor": "selectivecolor=reds='0 0 0 0'",
    "lut1d": "lut1d=file={cube1}",
    "histeq": "histeq",
    "normalize": "normalize",
    "tonemap": "tonemap=none",
    "dctdnoiz": "dctdnoiz",
}
#: Filters that work in YUV and so must stay off the list.
YUV_CAPABLE = {
    "lutyuv": "lutyuv=y=val",
    "gblur": "gblur=sigma=1",
    "unsharp": "unsharp",
    "hue": "hue=h=0",
}

_CONVERSION = re.compile(r"\[auto_scale_\d+ @ \w+\] w:\d+ h:\d+ fmt:(\w+) .*-> .*fmt:(\w+) ")
_RGB_FORMAT = re.compile(r"^(rgb|bgr|gbr|argb|abgr|rgba|bgra)")


@pytest.fixture(scope="module")
def env():
    e = probe()
    if not e.available or shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg not usable")
    return e


@pytest.fixture(scope="module")
def cubes(tmp_path_factory):
    folder = tmp_path_factory.mktemp("cubes")
    (folder / "id3.cube").write_text(_CUBE_3D)
    (folder / "id1.cube").write_text(_CUBE_1D)
    return {"cube3": (folder / "id3.cube").as_posix(), "cube1": (folder / "id1.cube").as_posix()}


def _converts_to_rgb(env, name, invocation, cubes) -> bool:
    """Whether ffmpeg auto-inserts a YUV -> RGB scaler in front of the filter."""
    if name not in env.filters:
        pytest.skip(f"this ffmpeg has no {name!r} filter")
    result = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-v", "debug",
            "-f", "lavfi", "-i", "testsrc2=s=64x48:r=1,format=yuv420p",
            "-vf", invocation.format(**cubes),
            "-frames:v", "1", "-f", "null", "-",
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"{name}: {result.stderr[-400:]}"
    pairs = _CONVERSION.findall(result.stderr)
    return any(
        src.startswith("yuv") and _RGB_FORMAT.match(dst) for src, dst in pairs
    )


def test_every_listed_filter_has_an_invocation():
    assert set(INVOCATIONS) == set(RGB_DOMAIN_FILTERS)


@pytest.mark.parametrize("name", sorted(INVOCATIONS))
def test_a_listed_filter_is_auto_scaled_to_rgb(env, cubes, name):
    assert _converts_to_rgb(env, name, INVOCATIONS[name], cubes), name


@pytest.mark.parametrize("name", sorted(YUV_CAPABLE))
def test_a_yuv_capable_filter_is_not_auto_scaled(env, cubes, name):
    assert not is_rgb_domain((name,))
    assert not _converts_to_rgb(env, name, YUV_CAPABLE[name], cubes), name
