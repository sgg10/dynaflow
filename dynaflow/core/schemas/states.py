from dynaflow.core.constants import SCHEMA_URL


FAIL_STATE_SCHEMA = {
    "$schema": SCHEMA_URL,
    "allOf": [
        {"$ref": "StateParent"},
        {
            "type": "object",
            "properties": {
                "Type": {"const": "Fail"},
            },
            "required": ["Type"],
        },
    ],
}


SUCCEED_STATE_SCHEMA = {
    "$schema": SCHEMA_URL,
    "allOf": [
        {"$ref": "StateParent"},
        {"$ref": "InputOutputPathSchema"},
        {
            "type": "object",
            "properties": {
                "Type": {"const": "Succeed"},
            },
            "required": ["Type"],
        },
    ],
}


CHOICE_STATE_SCHEMA = {
    "$schema": SCHEMA_URL,
    "allOf": [
        {"$ref": "StateParent"},
        {"$ref": "InputOutputPathSchema"},
        {
            "type": "object",
            "properties": {
                "Choices": {"type": "array", "items": {"$ref": "ChoiceRule"}},
                "Default": {"type": "string"},
            },
            "required": ["Choices"],
        },
        {
            "type": "object",
            "properties": {
                "Type": {"const": "Choice"},
            },
            "required": ["Type"],
        },
    ],
}

WAIT_STATE_SCHEMA = {
    "$schema": SCHEMA_URL,
    "allOf": [
        {"$ref": "StateParent"},
        {"$ref": "InputOutputPathSchema"},
        {"$ref": "NextOrEndStateSchema"},
        {
            "type": "object",
            "properties": {
                "Seconds": {"anyOf": [{"type": "number"}, {"type": "string"}]}
            },
        },
        {
            "type": "object",
            "properties": {
                "Type": {"const": "Wait"},
            },
            "required": ["Type"],
        },
    ],
}

PASS_STATE_SCHEMA = {
    "$schema": SCHEMA_URL,
    "allOf": [
        {"$ref": "StateParent"},
        {"$ref": "InputOutputPathSchema"},
        {"$ref": "NextOrEndStateSchema"},
        {"$ref": "ParametersSchema"},
        {"$ref": "ResultPathSchema"},
        {
            "type": "object",
            "properties": {
                "Type": {"const": "Pass"},
            },
            "required": ["Type"],
        },
    ],
}

TASK_STATE_SCHEMA = {
    "$schema": SCHEMA_URL,
    "allOf": [
        {"$ref": "FullStateSchema"},
        {
            "type": "object",
            "properties": {
                "Function": {
                    "type": "object",
                    "properties": {
                        "Name": {"type": "string"},
                        "Version": {"oneOf": [{"type": "integer"}, {"type": "string"}]},
                    },
                    "required": ["Name"],
                    "additionalProperties": True,
                },
            },
        },
        {
            "type": "object",
            "properties": {
                "Type": {"const": "Task"},
            },
            "required": ["Type"],
        },
    ],
    "required": ["Function"],
}

BASE_FLOW_SCHEMA = {
    "$schema": SCHEMA_URL,
    "type": "object",
    "properties": {
        "StartAt": {"type": "string"},
        "Comment": {"type": "string"},
        "Version": {"type": "string"},
        "States": {
            "type": "object",
            "additionalProperties": {
                "anyOf": [
                    {"$ref": "FailStateSchema"},
                    {"$ref": "SucceedStateSchema"},
                    {"$ref": "ChoiceStateSchema"},
                    {"$ref": "WaitStateSchema"},
                    {"$ref": "PassStateSchema"},
                    {"$ref": "TaskStateSchema"},
                    {"$ref": "ParallelStateSchema"},
                    {"$ref": "MapStateSchema"},
                ]
            },
        },
    },
    "required": ["StartAt", "States"],
}

PARALLEL_STATE_SCHEMA = {
    "$schema": SCHEMA_URL,
    "allOf": [
        {"$ref": "FullStateSchema"},
        {
            "type": "object",
            "properties": {
                "Branches": {"type": "array", "items": {"$ref": "BaseFlowSchema"}},
            },
            "required": ["Branches"],
        },
        {
            "type": "object",
            "properties": {
                "Type": {"const": "Parallel"},
            },
            "required": ["Type"],
        },
    ],
    "required": ["Branches"],
}

MAP_STATE_SCHEMA = {
    "$schema": SCHEMA_URL,
    "allOf": [
        {"$ref": "FullStateSchema"},
        {
            "type": "object",
            "properties": {
                "ItemProcessor": {"$ref": "BaseFlowSchema"},
                "ItemsPath": {"type": "string"},
                # "MaxConcurrency": {"type": "integer"},
                # "BatchSize": {"type": "integer"},
                # "TimeoutSeconds": {"type": "integer"},
                # "Retry": {"$ref": "RetrySchema"},
                # "Catch": {"$ref": "CatchSchema"},
                # "IteratorState": {"$ref": "BaseFlowSchema"},
                # "End": {"type": "boolean"},
            },
            "required": ["ItemsPath", "ItemProcessor"],
        },
        {
            "type": "object",
            "properties": {
                "Type": {"const": "Map"},
            },
            "required": ["Type"],
        },
    ],
    "required": ["ItemsPath", "ItemProcessor"],
}

STATE_SCHEMAS_MAP = {
    "BaseFlowSchema": BASE_FLOW_SCHEMA,
    "FailStateSchema": FAIL_STATE_SCHEMA,
    "SucceedStateSchema": SUCCEED_STATE_SCHEMA,
    "ChoiceStateSchema": CHOICE_STATE_SCHEMA,
    "WaitStateSchema": WAIT_STATE_SCHEMA,
    "PassStateSchema": PASS_STATE_SCHEMA,
    "TaskStateSchema": TASK_STATE_SCHEMA,
    "ParallelStateSchema": PARALLEL_STATE_SCHEMA,
    "MapStateSchema": MAP_STATE_SCHEMA,
}
