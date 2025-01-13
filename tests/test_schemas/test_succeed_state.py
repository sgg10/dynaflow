import pytest
import jsonschema
from referencing import Registry, Resource


from dynaflow.core.schemas.bases import BASE_SCHEMAS_MAP
from dynaflow.core.schemas.states import SUCCEED_STATE_SCHEMA


REGISTRY = Registry().with_resources(
    [
        (name, Resource.from_contents(schema))
        for name, schema in BASE_SCHEMAS_MAP.items()
    ]
)

VALIDATOR = jsonschema.Draft7Validator(SUCCEED_STATE_SCHEMA, registry=REGISTRY)


def test_succeed_state():
    data = {
        "Type": "Succeed",
        "InputPath": "$",
        "OutputPath": "$",
    }

    assert VALIDATOR.is_valid(data)
