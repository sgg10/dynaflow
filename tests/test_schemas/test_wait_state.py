import pytest
import jsonschema
from referencing import Registry, Resource


from dynaflow.core.schemas.bases import BASE_SCHEMAS_MAP
from dynaflow.core.schemas.states import WAIT_STATE_SCHEMA


REGISTRY = Registry().with_resources(
    [
        (name, Resource.from_contents(schema))
        for name, schema in BASE_SCHEMAS_MAP.items()
    ]
)

VALIDATOR = jsonschema.Draft7Validator(WAIT_STATE_SCHEMA, registry=REGISTRY)


def test_success_wait_state():
    samples = [
        {
            "Type": "Wait",
            "Seconds": 10,
            "Next": "NextState",
        },
        {
            "Type": "Wait",
            "Seconds": 10,
            "InputPath": "$.input",
            "OutputPath": "$.output",
            "End": True,
        },
    ]

    assert all(VALIDATOR.is_valid(data) for data in samples)


def test_fail_wait_state():
    samples = [
        {
            "Type": "Wait",
            "Seconds": 10,
        },
        {
            "Type": "Wait",
            "Seconds": 10,
            "InputPath": "$.input",
            "OutputPath": "$.output",
        },
    ]

    assert all(not VALIDATOR.is_valid(data) for data in samples)
