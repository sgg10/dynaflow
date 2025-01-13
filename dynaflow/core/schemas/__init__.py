from referencing import Registry, Resource

from dynaflow.core.schemas.bases import BASE_SCHEMAS_MAP
from dynaflow.core.schemas.states import STATE_SCHEMAS_MAP, BASE_FLOW_SCHEMA

FLOW_SCHEMA = BASE_FLOW_SCHEMA
REGISTRY = Registry().with_resources(
    [
        (name, Resource.from_contents(schema))
        for name, schema in BASE_SCHEMAS_MAP.items()
    ]
    + [
        (name, Resource.from_contents(schema))
        for name, schema in STATE_SCHEMAS_MAP.items()
    ]
)
