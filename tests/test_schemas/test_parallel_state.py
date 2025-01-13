import pytest
import jsonschema

from dynaflow.core.schemas import REGISTRY
from dynaflow.core.schemas.states import PARALLEL_STATE_SCHEMA

VALIDATOR = jsonschema.Draft7Validator(PARALLEL_STATE_SCHEMA, registry=REGISTRY)


def test_success_parallel_state():

    samples = [
        {
            "Type": "Parallel",
            "Branches": [
                {
                    "StartAt": "Branch1",
                    "States": {
                        "Branch1": {
                            "Type": "Task",
                            "Function": {"Name": "function_name"},
                            "Next": "NextState",
                        }
                    },
                },
                {
                    "StartAt": "Branch2",
                    "States": {
                        "Branch2": {
                            "Type": "Task",
                            "Function": {"Name": "function_name"},
                            "Next": "NextState",
                        }
                    },
                },
            ],
            "Next": "NextState",
        },
        {
            "Type": "Parallel",
            "Branches": [
                {
                    "StartAt": "Branch1",
                    "States": {
                        "Branch1": {
                            "Type": "Task",
                            "Function": {"Name": "function_name"},
                            "Next": "NextState",
                        }
                    },
                },
                {
                    "StartAt": "Branch2",
                    "States": {
                        "Branch2": {
                            "Type": "Task",
                            "Function": {"Name": "function_name"},
                            "Next": "NextState",
                        }
                    },
                },
            ],
            "InputPath": "$.input",
            "OutputPath": "$.output",
            "End": True,
        },
    ]

    assert all(VALIDATOR.is_valid(data) for data in samples)


def test_fail_parallel_state():
    samples = [
        {
            "Type": "Parallel",
            "Next": "NextState",
        },
        {
            "Type": "Parallel",
            "Branches": [
                {
                    "StartAt": "Branch1",
                    "States": {
                        "Branch1": {
                            "Type": "Task",
                            "Function": {"Name": "function_name"},
                            "Next": "NextState",
                        }
                    },
                },
                {
                    "StartAt": "Branch2",
                    "States": {
                        "Branch2": {
                            "Type": "Task",
                            "Function": {"Name": "function_name"},
                            "Next": "NextState",
                        }
                    },
                },
            ],
            "InputPath": "$.input",
            "OutputPath": "$.output",
        },
    ]

    assert all(not VALIDATOR.is_valid(data) for data in samples)
