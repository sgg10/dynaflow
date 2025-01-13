import pytest
import jsonschema
from referencing import Registry, Resource

from dynaflow.core.schemas.bases import (
    GENERAL_STATE_SCHEMA,
    INPUT_OUTPUT_PATH_SCHEMA,
    CHOICE_SIMPLE_RULE,
    CHOICE_NOT_RULE,
    CHOICE_AND_RULE,
    CHOICE_OR_RULE,
    CHOICE_OUTER_RULE,
    CHOICE_RULE,
)

from dynaflow.core.schemas.states import CHOICE_STATE_SCHEMA


def test_success_choice_simple_rule():
    schema = CHOICE_SIMPLE_RULE

    registry = Registry().with_resources([])
    validator = jsonschema.Draft7Validator(schema, resolver=registry)

    samples = [
        {"Variable": "var", "boolean_equals": True},
        {"Variable": "var", "numeric_equals": 1},
        {"Variable": "var", "string_equals": "value", "Next": "next"},
    ]

    assert all(validator.is_valid(data) for data in samples)


def test_fail_choice_simple_rule():
    schema = CHOICE_SIMPLE_RULE

    registry = Registry().with_resources([])
    validator = jsonschema.Draft7Validator(schema, resolver=registry)

    samples = [
        {"Variable": "var", "boolean_equals": "True"},
        {"Variable": "var", "numeric_equals": "1"},
        {"Variable": "var", "string_equals": 1, "Next": "next"},
    ]

    assert all(not validator.is_valid(data) for data in samples)


def test_success_not_rule():

    sub_schemas = {
        "ChoiceSimpleRule": CHOICE_SIMPLE_RULE,
    }

    schema = CHOICE_NOT_RULE

    registry = Registry().with_resources(
        [(name, Resource.from_contents(schema)) for name, schema in sub_schemas.items()]
    )
    validator = jsonschema.Draft7Validator(schema, registry=registry)

    samples = [
        {"Not": {"Variable": "var", "boolean_equals": True}, "Next": "next"},
        {"Not": {"Variable": "var", "numeric_equals": 1}, "Next": "next"},
        {"Not": {"Variable": "var", "string_equals": "value"}, "Next": "next"},
    ]

    assert all(validator.is_valid(data) for data in samples)


def test_fail_not_rule():

    sub_schemas = {
        "ChoiceSimpleRule": CHOICE_SIMPLE_RULE,
    }

    schema = CHOICE_NOT_RULE

    registry = Registry().with_resources(
        [(name, Resource.from_contents(schema)) for name, schema in sub_schemas.items()]
    )
    validator = jsonschema.Draft7Validator(schema, registry=registry)

    samples = [
        {"Not": {"Variable": "var", "boolean_equals": "True"}, "Next": "next"},
        {"Not": {"Variable": "var", "numeric_equals": "1"}, "Next": "next"},
        {"Not": {"Variable": "var", "string_equals": 1}},
    ]

    assert all(not validator.is_valid(data) for data in samples)


def test_success_and_rule():

    sub_schemas = {
        "ChoiceSimpleRule": CHOICE_SIMPLE_RULE,
    }

    schema = CHOICE_AND_RULE

    registry = Registry().with_resources(
        [(name, Resource.from_contents(schema)) for name, schema in sub_schemas.items()]
    )
    validator = jsonschema.Draft7Validator(schema, registry=registry)

    samples = [
        {
            "And": [
                {"Variable": "var1", "boolean_equals": True},
                {"Variable": "var2", "numeric_equals": 1},
            ],
            "Next": "next",
        },
        {
            "And": [
                {"Variable": "var1", "numeric_equals": 1},
                {"Variable": "var2", "string_equals": "value"},
            ],
            "Next": "next",
        },
    ]

    assert all(validator.is_valid(data) for data in samples)


def test_fail_and_rule():

    sub_schemas = {
        "ChoiceSimpleRule": CHOICE_SIMPLE_RULE,
    }

    schema = CHOICE_AND_RULE

    registry = Registry().with_resources(
        [(name, Resource.from_contents(schema)) for name, schema in sub_schemas.items()]
    )
    validator = jsonschema.Draft7Validator(schema, registry=registry)

    samples = [
        {
            "And": [
                {"Variable": "var1", "boolean_equals": "True"},
                {"Variable": "var2", "numeric_equals": 1},
            ]
        },
        {
            "And": [
                {"Variable": "var1", "numeric_equals": 1},
                {"Variable": "var2", "string_equals": 1},
            ],
            "Next": "next",
        },
    ]

    assert all(not validator.is_valid(data) for data in samples)


def test_success_or_rule():

    sub_schemas = {
        "ChoiceSimpleRule": CHOICE_SIMPLE_RULE,
    }

    schema = CHOICE_OR_RULE

    registry = Registry().with_resources(
        [(name, Resource.from_contents(schema)) for name, schema in sub_schemas.items()]
    )
    validator = jsonschema.Draft7Validator(schema, registry=registry)

    samples = [
        {
            "Or": [
                {"Variable": "var1", "boolean_equals": True},
                {"Variable": "var2", "numeric_equals": 1},
            ],
            "Next": "next",
        },
        {
            "Or": [
                {"Variable": "var1", "numeric_equals": 1},
                {"Variable": "var2", "string_equals": "value"},
            ],
            "Next": "next",
        },
    ]

    assert all(validator.is_valid(data) for data in samples)


def test_fail_or_rule():

    sub_schemas = {
        "ChoiceSimpleRule": CHOICE_SIMPLE_RULE,
    }

    schema = CHOICE_OR_RULE

    registry = Registry().with_resources(
        [(name, Resource.from_contents(schema)) for name, schema in sub_schemas.items()]
    )
    validator = jsonschema.Draft7Validator(schema, registry=registry)

    samples = [
        {
            "Or": [
                {"Variable": "var1", "boolean_equals": "True"},
                {"Variable": "var2", "numeric_equals": 1},
            ]
        },
        {
            "Or": [
                {"Variable": "var1", "numeric_equals": 1},
                {"Variable": "var2", "string_equals": 1},
            ],
            "Next": "next",
        },
    ]

    assert all(not validator.is_valid(data) for data in samples)


def test_success_outer_rule():

    sub_schemas = {
        "ChoiceSimpleRule": CHOICE_SIMPLE_RULE,
    }

    schema = CHOICE_OUTER_RULE

    registry = Registry().with_resources(
        [(name, Resource.from_contents(schema)) for name, schema in sub_schemas.items()]
    )
    validator = jsonschema.Draft7Validator(schema, registry=registry)

    samples = [
        {"Variable": "var", "boolean_equals": True, "Next": "next"},
        {"Variable": "var", "numeric_equals": 1, "Next": "next"},
        {"Variable": "var", "string_equals": "value", "Next": "next"},
    ]

    assert all(validator.is_valid(data) for data in samples)


def test_fail_outer_rule():

    sub_schemas = {
        "ChoiceSimpleRule": CHOICE_SIMPLE_RULE,
    }

    schema = CHOICE_OUTER_RULE

    registry = Registry().with_resources(
        [(name, Resource.from_contents(schema)) for name, schema in sub_schemas.items()]
    )
    validator = jsonschema.Draft7Validator(schema, registry=registry)

    samples = [
        {"Variable": "var", "boolean_equals": "True", "Next": "next"},
        {"Variable": "var", "numeric_equals": "1", "Next": "next"},
        {"Variable": "var", "string_equals": 1},
    ]

    assert all(not validator.is_valid(data) for data in samples)


def test_success_choice_rule():

    sub_schemas = {
        "ChoiceSimpleRule": CHOICE_SIMPLE_RULE,
        "ChoiceNotRule": CHOICE_NOT_RULE,
        "ChoiceAndRule": CHOICE_AND_RULE,
        "ChoiceOrRule": CHOICE_OR_RULE,
        "ChoiceOuterRule": CHOICE_OUTER_RULE,
    }

    schema = CHOICE_RULE

    registry = Registry().with_resources(
        [(name, Resource.from_contents(schema)) for name, schema in sub_schemas.items()]
    )
    validator = jsonschema.Draft7Validator(schema, registry=registry)

    samples = [
        {"Variable": "var", "boolean_equals": True, "Next": "next"},
        {"Variable": "var", "numeric_equals": 1, "Next": "next"},
        {"Variable": "var", "string_equals": "value", "Next": "next"},
        {"Not": {"Variable": "var", "boolean_equals": True}, "Next": "next"},
        {
            "And": [
                {"Variable": "var1", "boolean_equals": True},
                {"Variable": "var2", "numeric_equals": 1},
            ],
            "Next": "next",
        },
        {
            "Or": [
                {"Variable": "var1", "boolean_equals": True},
                {"Variable": "var2", "numeric_equals": 1},
            ],
            "Next": "next",
        },
        {"Variable": "var", "boolean_equals": True, "Next": "next"},
    ]

    assert all(validator.is_valid(data) for data in samples)


def test_fail_choice_rule():

    sub_schemas = {
        "ChoiceSimpleRule": CHOICE_SIMPLE_RULE,
        "ChoiceNotRule": CHOICE_NOT_RULE,
        "ChoiceAndRule": CHOICE_AND_RULE,
        "ChoiceOrRule": CHOICE_OR_RULE,
        "ChoiceOuterRule": CHOICE_OUTER_RULE,
    }

    schema = CHOICE_RULE

    registry = Registry().with_resources(
        [(name, Resource.from_contents(schema)) for name, schema in sub_schemas.items()]
    )
    validator = jsonschema.Draft7Validator(schema, registry=registry)

    samples = [
        {"Variable": "var", "boolean_equals": "True", "Next": "next"},
        {"Variable": "var", "numeric_equals": "1", "Next": "next"},
        {"Variable": "var", "string_equals": 1},
        {"Not": {"Variable": "var", "boolean_equals": "True"}, "Next": "next"},
        {
            "And": [
                {"Variable": "var1", "boolean_equals": "True"},
                {"Variable": "var2", "numeric_equals": 1},
            ]
        },
        {
            "Or": [
                {"Variable": "var1", "boolean_equals": "True"},
                {"Variable": "var2", "numeric_equals": 1},
            ],
            "Next": "next",
        },
        {"Variable": "var", "boolean_equals": "True", "Next": "next"},
    ]

    assert all(not validator.is_valid(data) for data in samples)


def test_success_choice_state():

    sub_schemas = {
        "ChoiceSimpleRule": CHOICE_SIMPLE_RULE,
        "ChoiceNotRule": CHOICE_NOT_RULE,
        "ChoiceAndRule": CHOICE_AND_RULE,
        "ChoiceOrRule": CHOICE_OR_RULE,
        "ChoiceOuterRule": CHOICE_OUTER_RULE,
        "ChoiceRule": CHOICE_RULE,
        "StateParent": GENERAL_STATE_SCHEMA,
        "InputOutputPathSchema": INPUT_OUTPUT_PATH_SCHEMA,
    }

    schema = CHOICE_STATE_SCHEMA

    registry = Registry().with_resources(
        [(name, Resource.from_contents(schema)) for name, schema in sub_schemas.items()]
    )
    validator = jsonschema.Draft7Validator(schema, registry=registry)

    samples = [
        {
            "Type": "Choice",
            "Comment": "A simple choice state",
            "Choices": [
                {"Variable": "var", "boolean_equals": True, "Next": "next"},
                {"Variable": "var", "numeric_equals": 1, "Next": "next"},
                {"Variable": "var", "string_equals": "value", "Next": "next"},
                {"Not": {"Variable": "var", "boolean_equals": True}, "Next": "next"},
                {
                    "And": [
                        {"Variable": "var1", "boolean_equals": True},
                        {"Variable": "var2", "numeric_equals": 1},
                    ],
                    "Next": "next",
                },
                {
                    "Or": [
                        {"Variable": "var1", "boolean_equals": True},
                        {"Variable": "var2", "numeric_equals": 1},
                    ],
                    "Next": "next",
                },
                {"Variable": "var", "boolean_equals": True, "Next": "next"},
            ],
            "Default": "default",
        },
        {
            "Type": "Choice",
            "Comment": "A simple choice state",
            "InputPath": "$.input",
            "OutputPath": "$.output",
            "Choices": [{"Variable": "$.var", "boolean_equals": True, "Next": "next"}],
        },
    ]

    assert all(validator.is_valid(data) for data in samples)


def test_fail_choice_state():

    sub_schemas = {
        "ChoiceSimpleRule": CHOICE_SIMPLE_RULE,
        "ChoiceNotRule": CHOICE_NOT_RULE,
        "ChoiceAndRule": CHOICE_AND_RULE,
        "ChoiceOrRule": CHOICE_OR_RULE,
        "ChoiceOuterRule": CHOICE_OUTER_RULE,
        "ChoiceRule": CHOICE_RULE,
        "StateParent": GENERAL_STATE_SCHEMA,
        "InputOutputPathSchema": INPUT_OUTPUT_PATH_SCHEMA,
    }

    schema = CHOICE_STATE_SCHEMA

    registry = Registry().with_resources(
        [(name, Resource.from_contents(schema)) for name, schema in sub_schemas.items()]
    )
    validator = jsonschema.Draft7Validator(schema, registry=registry)

    samples = [
        {
            "Type": "Choice",
            "Comment": "A simple choice state",
            "Choices": [
                {"Variable": "var", "boolean_equals": "True", "Next": "next"},
                {"Variable": "var", "numeric_equals": "1", "Next": "next"},
                {"Variable": "var", "string_equals": 1, "Next": "next"},
                {"Not": {"Variable": "var", "boolean_equals": "True"}},
                {
                    "And": [
                        {"Variable": "var1", "boolean_equals": "True"},
                        {"Variable": "var2", "numeric_equals": 1},
                    ]
                },
                {
                    "Or": [
                        {"Variable": "var1", "boolean_equals": "True"},
                        {"Variable": "var2", "numeric_equals": 1},
                    ],
                    "Next": "next",
                },
                {"Variable": "var", "boolean_equals": "True"},
            ],
        },
        {
            "Type": "Choice",
            "Comment": "A simple choice state",
            "InputPath": "$.input",
            "OutputPath": "$.output",
            "Choices": [{"Variable": "$.var", "boolean_equals": "True"}],
        },
    ]

    assert all(not validator.is_valid(data) for data in samples)
