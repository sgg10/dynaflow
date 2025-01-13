import pytest
import jsonschema
from referencing import Registry, Resource


from dynaflow.core.schemas.bases import BASE_SCHEMAS_MAP
from dynaflow.core.schemas.states import TASK_STATE_SCHEMA


REGISTRY = Registry().with_resources(
    [
        (name, Resource.from_contents(schema))
        for name, schema in BASE_SCHEMAS_MAP.items()
    ]
)

VALIDATOR = jsonschema.Draft7Validator(TASK_STATE_SCHEMA, registry=REGISTRY)


def test_success_task_state():
    samples = [
        {
            "Type": "Task",
            "Function": {"Name": "function_name"},
            "Next": "NextState",
        },
        {
            "Type": "Task",
            "Function": {
                "Name": "function_name",
                "Version": "1.0",
            },
            "Next": "NextState",
        },
        {
            "Type": "Task",
            "Function": {
                "Name": "function_name",
                "Version": 1,
            },
            "Next": "NextState",
        },
        {
            "Type": "Task",
            "InputPath": "$.input",
            "OutputPath": "$.output",
            "Parameters": {"key": "$.value", "older_users": "$.user[?(@.age > 60)]"},
            "ResultPath": "$.result",
            "ResultSelector": {"key": "$.value"},
            "Function": {
                "Name": "function_name",
                "Version": 1,
            },
            "Retry": [
                {
                    "ErrorEquals": ["ErrorA", "ErrorB"],
                    "IntervalSeconds": 1,
                    "BackoffRate": 2,
                    "MaxAttempts": 2,
                },
                {"ErrorEquals": ["ErrorC"], "IntervalSeconds": 5},
            ],
            "Catch": [{"ErrorEquals": ["States.ALL"], "Next": "Z"}],
            "End": True,
        },
    ]

    assert all(VALIDATOR.is_valid(data) for data in samples)


def test_fail_task_state():
    samples = [
        {
            "Type": "Task",
            "Function": {
                "Name": "function_name",
            },
            "Next": "NextState",
            "End": True,
        },
        {
            "Type": "Task",
            "End": True,
        },
        {
            "Type": "Task",
            "Function": {"Name": "function_name"},
            "InputPath": "$.input",
            "OutputPath": "$.output",
            "Parameters": {"key": "$.value", "older_users": "$.user[?(@.age > 60)]"},
            "ResultPath": "$.result",
            "ResultSelector": {"key": "$.value"},
        },
    ]

    assert all(not VALIDATOR.is_valid(data) for data in samples)
