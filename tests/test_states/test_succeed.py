import pytest

from dynaflow.core.states import SucceedState


def test_succeed_state():
    definition = {
        "Type": "Succeed",
        "InputPath": "$",
        "OutputPath": "$.key",
    }

    state = SucceedState(definition)

    result = state.execute({"key": "value"})
    assert result == "value"
    assert state.get_next_state() == None
    assert state.is_terminal()
