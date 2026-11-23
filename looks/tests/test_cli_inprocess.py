"""``looks.cli`` command functions called in-process (the subprocess tests in test_cli.py are invisible to coverage)."""

import importlib.util

import pytest

from looks import cli
from looks import environment as envmod
from looks.environment import FfmpegEnv as Environment, Licence


# --- env ----------------------------------------------------------------------


def test_env_reports_an_unusable_ffmpeg(monkeypatch):
    monkeypatch.setattr(
        envmod, "probe", lambda ffmpeg="ffmpeg": Environment(notes=("not found",))
    )
    out = cli.env("nosuch")
    assert out.startswith("ffmpeg   : NOT USABLE (nosuch)") and "not found" in out


def test_env_reports_a_usable_ffmpeg_with_notes(monkeypatch):
    fake = Environment(
        path="/x/ffmpeg",
        version="ffmpeg version 7.0",
        licence=Licence.UNKNOWN,
        filters=frozenset({"scale", "eq"}),
        notes=("careful",),
    )
    monkeypatch.setattr(envmod, "probe", lambda ffmpeg="ffmpeg": fake)
    assert fake.available
    out = cli.env()
    assert "path     : /x/ffmpeg" in out and "filters  : 2" in out
    assert "note     : careful" in out


# --- check --------------------------------------------------------------------


def test_check_clean_chain_message_and_quiet():
    assert cli.check(["curves", "lut3d"]) == "none of these needs a GPL build"
    assert cli.check(["curves"], quiet=True) == ""


def test_check_gated_chain_exits_with_names_and_substitutions():
    with pytest.raises(SystemExit) as e:
        cli.check(["scale", "eq"])
    msg = str(e.value)
    assert "eq" in msg and "need a GPL ffmpeg build" in msg and "LGPL-clean" in msg
    with pytest.raises(SystemExit) as q:
        cli.check(["eq"], quiet=True)
    assert str(q.value) == "eq"


def test_check_unknown_filter_is_a_one_line_refusal():
    with pytest.raises(SystemExit, match="not known ffmpeg filters"):
        cli.check(["nosuchfilter"])


def test_check_against_a_probed_ffmpeg_uses_its_filter_list(monkeypatch):
    fake = Environment(path="/x/ffmpeg", filters=frozenset({"curves"}))
    monkeypatch.setattr(envmod, "probe", lambda ffmpeg="ffmpeg": fake)
    assert cli.check(["curves"], ffmpeg="x") == "none of these needs a GPL build"
    unusable = Environment()
    monkeypatch.setattr(envmod, "probe", lambda ffmpeg="ffmpeg": unusable)
    assert cli.check(["curves"], ffmpeg="x") == "none of these needs a GPL build"


# --- motion -------------------------------------------------------------------


def test_motion_pan_compiles_to_a_crop():
    out = cli.motion(["0:0,0,0.5,0.5", "2:0.5,0.5,0.5,0.5"])
    assert "crop" in out


def test_motion_zoom_needs_output_and_fps_and_compiles_zoompan():
    out = cli.motion(["0:0,0,1,1", "2:0.25,0.25,0.5,0.5"], output="1920x1080", fps=25)
    assert "zoompan" in out


@pytest.mark.parametrize("bad", ["nonsense", "0:1,2,3"])
def test_motion_unreadable_keyframe(bad):
    with pytest.raises(SystemExit, match="cannot read .* as a keyframe"):
        cli.motion([bad])


def test_motion_unreadable_size():
    with pytest.raises(SystemExit, match="as a size"):
        cli.motion(["0:0,0,1,1"], output="big")


def test_motion_uncompilable_path_is_a_clean_refusal():
    with pytest.raises(SystemExit):
        cli.motion(["0:0,0,1,1", "2:0.25,0.25,0.5,0.5"])  # a zoom with no output size


# --- terms / place / flicker / ledger -------------------------------------------


def test_terms_prints_every_component_with_a_tier():
    out = cli.terms("moviepy")
    assert "moviepy/" in out and "spdx" in out and "tier" in out and "coupling" in out


def test_place_with_sizes_and_presets_and_noop():
    assert cli.place("1920x1080", "1080x1920")
    assert cli.place("1920x1080", "1080x1920", mode="fill", backdrop="ff0000")
    assert cli.place("1920x1080", "1920x1080") == "(no-op: the source is already the target)"
    from looks.geometry import SOCIAL_SIZES

    assert cli.place("1920x1080", next(iter(SOCIAL_SIZES)))


def test_unverified_and_disclaimer_are_nonempty_text():
    assert cli.unverified().startswith("- ")
    assert len(cli.disclaimer()) > 20


def test_command_table_maps_names_to_callables():
    assert set(cli.COMMANDS) == {
        "env", "check", "terms", "place", "motion", "measure", "flicker", "unverified", "disclaimer",
    }
    assert all(callable(f) for f in cli.COMMANDS.values())


def test_main_dispatches_in_process(capsys):
    if importlib.util.find_spec("cw") is None:
        pytest.skip("the CLI extra (`cw`) is not installed")
    assert cli.main(["check", "curves"]) in (0, None)
    assert "none of these needs a GPL build" in capsys.readouterr().out


@pytest.mark.xfail(strict=True, reason="looks#71: a non-numeric time escapes as a ValueError traceback")
def test_motion_non_numeric_time_is_a_clean_refusal():
    with pytest.raises(SystemExit, match="cannot read .* as a keyframe"):
        cli.motion(["x:0,0,1,1"])
