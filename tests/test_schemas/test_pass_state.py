import pytest
import jsonschema
from referencing import Registry, Resource


from dynaflow.core.schemas.bases import BASE_SCHEMAS_MAP
from dynaflow.core.schemas.states import PASS_STATE_SCHEMA


REGISTRY = Registry().with_resources(
    [
        (name, Resource.from_contents(schema))
        for name, schema in BASE_SCHEMAS_MAP.items()
    ]
)

VALIDATOR = jsonschema.Draft7Validator(PASS_STATE_SCHEMA, registry=REGISTRY)


def test_success_pass_state():
    samples = [
        {
            "Type": "Pass",
            "Next": "NextState",
        },
        {
            "Type": "Pass",
            "InputPath": "$.input",
            "OutputPath": "$.output",
            "End": True,
        },
        {
            "Type": "Pass",
            "InputPath": "$.input",
            "OutputPath": "$.output",
            "Parameters": {"key": "value"},
            "ResultPath": "$.result",
            "Next": "NextState",
        },
    ]

    assert all(VALIDATOR.is_valid(data) for data in samples)


def test_fail_pass_state():
    samples = [
        {
            "Type": "Pass",
            "InputPath": "$.input",
            "OutputPath": "$.output",
            "Parameters": {"key": "value"},
            "ResultPath": "$.result",
        },
        {
            "Type": "Pass",
            "Next": "NextState",
            "InputPath": "$.input",
            "OutputPath": "$.output",
            "Parameters": {"key": "value"},
            "ResultPath": "$.result",
            "End": True,
        },
    ]

    assert all(not VALIDATOR.is_valid(data) for data in samples)
