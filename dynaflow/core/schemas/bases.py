from dynaflow.core.constants import SCHEMA_URL
from dynaflow.core.logic.conditions import generate_logic_function_schemas

GENERAL_STATE_SCHEMA = {
    "$schema": SCHEMA_URL,
    "type": "object",
    "properties": {
        "Comment": {"type": "string"},
    },
}

INPUT_OUTPUT_PATH_SCHEMA = {
    "$schema": SCHEMA_URL,
    "type": "object",
    "properties": {
        "InputPath": {"type": "string"},
        "OutputPath": {"type": "string"},
    },
}

NEXT_OR_END_STATE_SCHEMA = {
    "$schema": SCHEMA_URL,
    "type": "object",
    "properties": {
        "Next": {"type": "string"},
        "End": {"type": "boolean"},
    },
    "oneOf": [{"required": ["Next"]}, {"required": ["End"]}],
    "not": {"required": ["Next", "End"]},
}

RESULT_PATH_SCHEMA = {
    "$schema": SCHEMA_URL,
    "type": "object",
    "properties": {"ResultPath": {"type": "string"}},
}

PARAMETERS_SCHEMA = {
    "$schema": SCHEMA_URL,
    "type": "object",
    "properties": {
        "Parameters": {
            "oneOf": [{"type": "object"}, {"type": "array"}, {"type": "string"}]
        }
    },
}

RESULT_SELECTOR_SCHEMA = {
    "$schema": SCHEMA_URL,
    "type": "object",
    "properties": {
        "ResultSelector": {
            "oneOf": [{"type": "object"}, {"type": "array"}, {"type": "string"}]
        }
    },
}

## Choice children schemas
CHOICE_SIMPLE_RULE = {
    "$schema": SCHEMA_URL,
    "type": "object",
    "allOf": [
        {
            "type": "object",
            "properties": {"Variable": {"type": "string"}},
            "required": ["Variable"],
        },
        {
            "type": "object",
            "oneOf": generate_logic_function_schemas(),
        },
    ],
}

CHOICE_NOT_RULE = {
    "$schema": SCHEMA_URL,
    "type": "object",
    "properties": {
        "Not": {"$ref": "ChoiceSimpleRule"},
        "Next": {"type": "string"},
    },
    "required": ["Not", "Next"],
}

CHOICE_AND_RULE = {
    "$schema": SCHEMA_URL,
    "type": "object",
    "properties": {
        "And": {"type": "array", "items": {"$ref": "ChoiceSimpleRule"}},
        "Next": {"type": "string"},
    },
    "required": ["And", "Next"],
}

CHOICE_OR_RULE = {
    "$schema": SCHEMA_URL,
    "type": "object",
    "properties": {
        "Or": {"type": "array", "items": {"$ref": "ChoiceSimpleRule"}},
        "Next": {"type": "string"},
    },
    "required": ["Or", "Next"],
}

CHOICE_OUTER_RULE = {
    "$schema": SCHEMA_URL,
    "type": "object",
    "allOf": [
        {"$ref": "ChoiceSimpleRule"},
        {
            "type": "object",
            "properties": {"Next": {"type": "string"}},
            "required": ["Next"],
        },
    ],
}

CHOICE_RULE = {
    "$schema": SCHEMA_URL,
    "anyOf": [
        {"$ref": "ChoiceSimpleRule"},
        {"$ref": "ChoiceNotRule"},
        {"$ref": "ChoiceAndRule"},
        {"$ref": "ChoiceOrRule"},
        {"$ref": "ChoiceOuterRule"},
    ],
}


FULL_STATE_SCHEMA = {
    "$schema": SCHEMA_URL,
    "allOf": [
        {"$ref": "StateParent"},
        {"$ref": "InputOutputPathSchema"},
        {"$ref": "NextOrEndStateSchema"},
        {"$ref": "ParametersSchema"},
        {"$ref": "ResultPathSchema"},
        {"$ref": "ResultSelectorSchema"},
        {
            "type": "object",
            "properties": {
                "Retry": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "ErrorEquals": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "IntervalSeconds": {
                                "type": "number",
                                "minimum": 0,
                                "default": 1,
                            },
                            "MaxAttempts": {
                                "type": "integer",
                                "minimum": 0,
                                "maximum": 10,
                                "default": 3,
                            },
                            "BackoffRate": {
                                "type": "number",
                                "minimum": 0,
                                "default": 2,
                            },
                            "MaxDelaySeconds": {
                                "type": "number",
                                "minimum": 0,
                                "default": 300,
                            },
                        },
                        "required": ["ErrorEquals"],
                    },
                },
                "Catch": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "ErrorEquals": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "Next": {"type": "string"},
                        },
                        "required": ["ErrorEquals", "Next"],
                    },
                },
            },
        },
    ],
}


BASE_SCHEMAS_MAP = {
    "StateParent": GENERAL_STATE_SCHEMA,
    "InputOutputPathSchema": INPUT_OUTPUT_PATH_SCHEMA,
    "NextOrEndStateSchema": NEXT_OR_END_STATE_SCHEMA,
    "ParametersSchema": PARAMETERS_SCHEMA,
    "ResultPathSchema": RESULT_PATH_SCHEMA,
    "ResultSelectorSchema": RESULT_SELECTOR_SCHEMA,
    "ChoiceSimpleRule": CHOICE_SIMPLE_RULE,
    "ChoiceNotRule": CHOICE_NOT_RULE,
    "ChoiceAndRule": CHOICE_AND_RULE,
    "ChoiceOrRule": CHOICE_OR_RULE,
    "ChoiceOuterRule": CHOICE_OUTER_RULE,
    "ChoiceRule": CHOICE_RULE,
    "FullStateSchema": FULL_STATE_SCHEMA,
}
