import pytest

from dynaflow.core.states import PassState


def test_pass_state_with_data_transform():
    definition = {
        "Type": "Pass",
        "Name": "PassState",
        "InputPath": "$.obj",
        "Parameters": "$.items[?(@ > 2)]",
        "ResultPath": "$.result",
        "OutputPath": "$.result",
        "Next": "NextState",
    }

    state = PassState(definition)

    result = state.execute({"obj": {"items": [1, 2, 3, 4]}})
    assert state.get_next_state() == "NextState"
    assert result == [3, 4]


def test_pass_state_with_complex_data_transform():
    definition = {
        "Type": "Pass",
        "Name": "PassState",
        "InputPath": "$",
        "Parameters": {
            "key": "$.items[?(@ > 2)]",
            "older_user_names": "$.user[?(@.age > 60)].name",
        },
        "ResultPath": "$.result",
        "OutputPath": "$.result",
        "Next": "NextState",
    }

    state = PassState(definition)

    result = state.execute(
        {
            "items": [1, 2, 3, 4],
            "user": [
                {"name": "John", "age": 25},
                {"name": "Jane", "age": 65},
                {"name": "Doe", "age": 70},
            ],
        }
    )
    assert state.get_next_state() == "NextState"
    assert result == {"key": [3, 4], "older_user_names": ["Jane", "Doe"]}
