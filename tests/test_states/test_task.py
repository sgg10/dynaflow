import time

import pytest

from dynaflow.core.states import TaskState


def test_task_state():
    definition = {
        "Type": "Task",
        "Function": {"Name": "add_one"},
        "InputPath": "$.input",
        "ResultPath": "$.x",
        "OutputPath": "$",
        "End": True,
    }

    state = TaskState(definition, lambda x: x + 1)

    result = state.execute({"input": {"x": 1}})
    assert result == {"x": 2}
