import pytest
import jsonschema

from dynaflow.core.schemas import REGISTRY
from dynaflow.core.schemas.states import MAP_STATE_SCHEMA

VALIDATOR = jsonschema.Draft7Validator(MAP_STATE_SCHEMA, registry=REGISTRY)


def test_success_map_state():
    samples = [
        {
            "Type": "Map",
            "ItemsPath": "$.items",
            "ItemProcessor": {
                "StartAt": "IteratorState",
                "States": {
                    "IteratorState": {
                        "Type": "Task",
                        "Function": {"Name": "function_name"},
                        "End": True,
                    }
                },
            },
            "End": True,
        },
        {
            "Type": "Map",
            "ItemsPath": "$.items",
            "ItemProcessor": {
                "StartAt": "IteratorState",
                "States": {
                    "IteratorState": {
                        "Type": "Task",
                        "Function": {"Name": "function_name"},
                        "Next": "NextState",
                    }
                },
            },
            "End": True,
        },
        {
            "Type": "Map",
            "InputPath": "$",
            "ItemsPath": "$.executions",
            "End": True,
            "ItemProcessor": {
                "StartAt": "Execute Package",
                "States": {
                    "Execute Package": {
                        "Type": "Task",
                        "Function": {"Name": "function_name", "Version": 1},
                        "End": True,
                    }
                },
            },
        },
    ]

    assert all(VALIDATOR.is_valid(data) for data in samples)


def test_fail_map_state():
    samples = [
        {
            "Type": "Map",
            "ItemsPath": "$.items",
            "Iterator": {
                "StartAt": "IteratorState",
                "States": {
                    "IteratorState": {
                        "Type": "Task",
                        "Function": {"Name": "function_name"},
                    }
                },
            },
            "End": True,
        },
        {
            "Type": "Map",
            "ItemsPath": "$.items",
            "ItemProcessor": {
                "StartAt": "IteratorState",
                "States": {
                    "IteratorState": {
                        "Type": "Task",
                        "Function": {"Name": "function_name"},
                        "Next": "NextState",
                    }
                },
            },
        },
        {
            "Type": "Map",
            "InputPath": "$",
            "ItemsPath": "$.executions",
            "End": True,
            "Next": "NextState",
            "ItemProcessor": {
                "StartAt": "Execute Package",
                "States": {
                    "Execute Package": {
                        "Type": "Task",
                        "Function": {"Name": "function_name", "Version": 1},
                    }
                },
            },
        },
    ]

    assert all(not VALIDATOR.is_valid(data) for data in samples)
