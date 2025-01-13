import time

import pytest

from dynaflow.core.states import WaitState


def test_wait_state():
    wait_time = 1

    definition = {
        "Type": "Wait",
        "Seconds": wait_time,
        "InputPath": "$.input",
        "OutputPath": "$",
        "End": True,
    }

    state = WaitState(definition)

    t0 = time.time()
    result = state.execute({"input": "value"})
    t1 = time.time() - t0
    assert result == "value"
    assert int(t1) == wait_time
