"""The parameter schema (issue #28): one declaration, read by checks and compilers.

Pure data plus `compile_look`'s refusal; no ffmpeg process is started except
where a test says so and skips without one.
"""

import math

import pytest

from looks.compile import CompileError, check_effect_params
from looks.params import (
    EFFECT_PARAMS,
    NO_DEFAULT,
    ParamError,
    check_params,
    with_defaults,
)
from looks.registry import REGISTRY
from looks.spec import Effect

ALL = [(e, p) for e, schema in sorted(EFFECT_PARAMS.items()) for p in sorted(schema)]
NUMERIC = [
    (e, p)
    for e, p in ALL
    if EFFECT_PARAMS[e][p].expects.startswith(("must be a number", "must not"))
    or EFFECT_PARAMS[e][p].expects.startswith("must be a whole")
]


def test_every_registered_effect_has_a_schema_and_the_reverse():
    """A new effect nobody declared would be silently unchecked."""
    assert set(EFFECT_PARAMS) == set(REGISTRY.effects())


@pytest.mark.parametrize("effect, key", ALL)
def test_a_declared_default_is_accepted_by_its_own_check(effect, key):
    param = EFFECT_PARAMS[effect][key]
    if param.default is not NO_DEFAULT:
        assert param.accepts(param.default), (effect, key, param.default)


@pytest.mark.parametrize("effect", sorted(EFFECT_PARAMS))
def test_an_unknown_key_is_refused_and_the_message_lists_the_known_ones(effect):
    with pytest.raises(CompileError, match="unknown parameter 'nonesuch'"):
        check_effect_params(Effect(name=effect, params={"nonesuch": 1}))


@pytest.mark.parametrize(
    "effect, params",
    [
        ("colorbalance", {"shadow": (0, 0, 0)}),  # singular: was an identity grade
        ("halation", {"sigmaa": 3}),
        ("grain", {"temporal": True}),
    ],
)
def test_the_misspellings_from_the_issue_are_refused(effect, params):
    with pytest.raises(CompileError, match=effect):
        check_effect_params(Effect(name=effect, params=params))


@pytest.mark.parametrize("effect, key", NUMERIC)
@pytest.mark.parametrize(
    "bad", [True, "0.5", math.inf, -math.inf, math.nan, None], ids=repr
)
def test_a_number_parameter_refuses_a_bool_a_string_and_a_non_finite(effect, key, bad):
    with pytest.raises(ParamError, match=key):
        check_params(effect, {key: bad})


def test_gate_weave_refuses_an_infinite_frequency():
    """It compiled to `sin(2*PI*inf*t)` and ffmpeg exited 0."""
    with pytest.raises(ParamError, match="frequency"):
        check_params("gate_weave", {"frequency": (math.inf, 1)})


def test_an_effect_without_a_schema_is_not_checked():
    check_params("a_callers_own_effect", {"anything": object()})


def test_defaults_fill_what_is_absent_and_leave_what_is_given():
    filled = with_defaults("halation", {"sigma": 3})
    assert filled["sigma"] == 3
    assert filled["threshold"] == EFFECT_PARAMS["halation"]["threshold"].default


def test_with_defaults_does_not_touch_its_input():
    given = {"sigma": 3}
    with_defaults("halation", given)
    assert given == {"sigma": 3}


def test_an_omitted_parameter_means_the_same_to_both_contrast_implementations():
    """Rule 29b: the default is the effect's, so it cannot differ per implementation."""
    assert with_defaults("contrast", {}) == {"amount": 1.0}


def test_the_plan_records_the_params_as_asked_not_with_defaults_filled_in():
    """Defaults are applied at compile time; `look_hash` and `Step.params` stay intent."""
    from looks.compile import compile_look
    from looks.environment import probe
    from looks.spec import ClipSpec, Look

    env = probe()
    if not env.available:
        pytest.skip("ffmpeg not usable")
    look = Look(steps=(Effect(name="grain"),))
    plan = compile_look(look, clip=ClipSpec(width=64, height=48, fps=10), env=env)
    assert dict(plan.steps[0].params) == {}
    assert "alls=8" in plan.steps[0].payload["filter"]
