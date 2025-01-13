import pytest

from dynaflow.core.states import FailState
from dynaflow.core.states.exceptions import FailError


def test_fail_state():
    definition = {
        "Type": "Fail",
    }

    state = FailState(definition)

    with pytest.raises(FailError):
        state.execute({})


def test_fail_state_with_additional_properties():
    definition = {
        "Type": "Fail",
        "Cause": "TEST-CAUSE",
        "Error": "TEST-ERROR",
    }

    state = FailState(definition)

    with pytest.raises(FailError) as exc_info:
        state.execute({})

        assert exc_info.value.cause == "TEST-CAUSE"
        assert exc_info.value.error == "TEST-ERROR"
        assert exc_info.message == "[TEST-ERROR] TEST-CAUSE"
