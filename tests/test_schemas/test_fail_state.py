import pytest
import jsonschema
from referencing import Registry, Resource


from dynaflow.core.schemas.bases import BASE_SCHEMAS_MAP
from dynaflow.core.schemas.states import FAIL_STATE_SCHEMA


REGISTRY = Registry().with_resources(
    [
        (name, Resource.from_contents(schema))
        for name, schema in BASE_SCHEMAS_MAP.items()
    ]
)

VALIDATOR = jsonschema.Draft7Validator(FAIL_STATE_SCHEMA, registry=REGISTRY)


def test_fail_state():
    data = {
        "Type": "Fail",
    }

    assert VALIDATOR.is_valid(data)
