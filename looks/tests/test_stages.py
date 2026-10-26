"""Stage-order validation (issue #26): warn on a departure, never reorder.

Pure data and the compiler. `probe()` runs ffmpeg for the compile tests.
"""

import warnings

import pytest

from looks.compile import compile_look
from looks.environment import probe
from looks.registry import REGISTRY
from looks.spec import ClipSpec, Effect, Look
from looks.stages import EFFECT_STAGES, StageOrderWarning, check_stage_order

CLIP = ClipSpec(width=64, height=48, fps=10, color_space="bt709")


def _names(*names):
    return [Effect(name=n) for n in names]


@pytest.mark.parametrize(
    "order",
    [
        ("fit", "saturation", "flatten", "lut3d", "posterize", "halation", "grain"),
        ("gradient_map", "vignette", "grain"),
        ("blur", "grain", "sharpen"),  # unstaged effects are unconstrained
        (),
    ],
)
def test_the_canonical_order_is_silent(order):
    assert check_stage_order(_names(*order)) == []


@pytest.mark.parametrize(
    "order, offender",
    [
        (("grain", "lut3d"), "lut3d"),  # grain would be colour-mapped
        (("grain", "posterize"), "posterize"),  # grain would be quantised away
        (("halation", "posterize"), "posterize"),  # optical before the look
        (("lut3d", "flatten"), "flatten"),  # flatten before the LUT
        (("saturation", "fit"), "fit"),  # geometry first
    ],
)
def test_each_measured_constraint_is_reported_on_the_later_effect(order, offender):
    (message,) = check_stage_order(_names(*order))
    assert message.startswith(offender)


def test_gate_weave_after_posterize_is_a_resample_not_a_stage_departure():
    assert "gate_weave" not in EFFECT_STAGES
    (message,) = check_stage_order(_names("posterize", "gate_weave"))
    assert "resamples" in message


def test_resampling_before_posterize_is_fine():
    assert check_stage_order(_names("gate_weave", "posterize")) == []


def test_a_resampler_after_posterize_is_reported_once():
    assert len(check_stage_order(_names("posterize", "fit"))) == 1


#: Registered effects deliberately outside the canon.
UNSTAGED = {"blur", "sharpen", "gate_weave"}


def test_every_registered_effect_is_staged_or_deliberately_not():
    """A typo, or a new effect nobody placed, would silently go unchecked."""
    registered = set(REGISTRY.effects())
    assert set(EFFECT_STAGES) <= registered
    assert registered - set(EFFECT_STAGES) == UNSTAGED


@pytest.mark.parametrize("later", ["lut3d", "gradient_map", "blur", "sharpen"])
def test_interpolating_after_posterize_is_reported(later):
    (message,) = check_stage_order(_names("posterize", later))
    assert "resamples" in message


def _compile(*names):
    env = probe()
    if not env.available:
        pytest.skip("ffmpeg not usable")
    return compile_look(
        Look(steps=_names(*names)), clip=CLIP, env=env
    )


def test_compile_look_warns_and_does_not_reorder():
    with pytest.warns(StageOrderWarning, match="gamma"):
        plan = _compile("grain", "gamma")
    assert [s.effect for s in plan.steps] == ["grain", "gamma"]


def test_the_warning_can_be_escalated_to_a_refusal():
    with warnings.catch_warnings():
        warnings.simplefilter("error", StageOrderWarning)
        with pytest.raises(StageOrderWarning):
            _compile("grain", "gamma")


def test_a_canonical_look_compiles_silently():
    with warnings.catch_warnings():
        warnings.simplefilter("error", StageOrderWarning)
        _compile("gamma", "grain")
