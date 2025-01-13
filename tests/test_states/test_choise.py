import pytest

from dynaflow.core.states import ChoiceState


def test_simple_choice_state():
    definition = {
        "Type": "Choice",
        "Name": "ChoiceState",
        "InputPath": "$",
        "Choices": [
            {
                "Variable": "$.var",
                "numeric_equals": 1,
                "Next": "NextState1",
            },
            {
                "Variable": "$.var",
                "numeric_equals": 2,
                "Next": "NextState2",
            },
            {
                "Variable": "$.var",
                "numeric_equals": 3,
                "Next": "NextState3",
            },
        ],
        "Default": "DefaultState",
    }

    state = ChoiceState(definition)

    assert state.get_next_state() == None
    assert state.choices == definition["Choices"]
    assert isinstance(state.choices, list)
    assert state.default == definition["Default"]
    assert isinstance(state.default, str)

    state.execute({"var": 1})
    assert state.get_next_state() == "NextState1"
    state.execute({"var": 2})
    assert state.get_next_state() == "NextState2"
    state.execute({"var": 3})
    assert state.get_next_state() == "NextState3"
    state.execute({"var": 4})
    assert state.get_next_state() == "DefaultState"


def test_and_choice_state():
    definition = {
        "Type": "Choice",
        "Name": "ChoiceState",
        "InputPath": "$",
        "Choices": [
            {
                "And": [
                    {
                        "Variable": "$.var1",
                        "numeric_greater_than": 1,
                    },
                    {
                        "Variable": "$.var2",
                        "numeric_less_than": 3,
                    },
                ],
                "Next": "NextState1",
            },
            {
                "And": [
                    {
                        "Variable": "$.var1",
                        "numeric_greater_than": 3,
                    },
                    {
                        "Variable": "$.var2",
                        "numeric_less_than": 5,
                    },
                ],
                "Next": "NextState2",
            },
        ],
        "Default": "DefaultState",
    }

    state = ChoiceState(definition)

    state.execute({"var1": 2, "var2": 2})
    assert state.get_next_state() == "NextState1"
    state.execute({"var1": 4, "var2": 4})
    assert state.get_next_state() == "NextState2"
    state.execute({"var1": 3, "var2": 6})
    assert state.get_next_state() == "DefaultState"


def test_or_choice_state():
    definition = {
        "Type": "Choice",
        "Name": "ChoiceState",
        "InputPath": "$",
        "Choices": [
            {
                "Or": [
                    {
                        "Variable": "$.var1",
                        "numeric_equals": 1,
                    },
                    {
                        "Variable": "$.var2",
                        "numeric_less_than": 1,
                    },
                ],
                "Next": "NextState1",
            },
            {
                "Or": [
                    {
                        "Variable": "$.var1",
                        "numeric_equals": 2,
                    },
                    {
                        "Variable": "$.var2",
                        "numeric_less_than": 3,
                    },
                ],
                "Next": "NextState2",
            },
        ],
        "Default": "DefaultState",
    }

    state = ChoiceState(definition)

    state.execute({"var1": 1, "var2": 4})
    assert state.get_next_state() == "NextState1"
    state.execute({"var1": 2, "var2": 2})
    assert state.get_next_state() == "NextState2"
    state.execute({"var1": 3, "var2": 6})
    assert state.get_next_state() == "DefaultState"


def test_not_choice_state():
    definition = {
        "Type": "Choice",
        "Name": "ChoiceState",
        "InputPath": "$",
        "Choices": [
            {
                "Not": {
                    "Variable": "$.var1",
                    "numeric_equals": 1,
                },
                "Next": "NextState1",
            },
            {
                "Not": {
                    "Variable": "$.var2",
                    "string_equals": "test",
                },
                "Next": "NextState2",
            },
        ],
        "Default": "DefaultState",
    }

    state = ChoiceState(definition)

    state.execute({"var1": 2})
    assert state.get_next_state() == "NextState1"
    state.execute({"var1": 1, "var2": "hello"})
    assert state.get_next_state() == "NextState2"
    state.execute({"var1": 1, "var2": "test"})
    assert state.get_next_state() == "DefaultState"
