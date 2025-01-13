import pytest
import jsonschema

from dynaflow.core.schemas import REGISTRY, FLOW_SCHEMA

VALIDATOR = jsonschema.Draft7Validator(FLOW_SCHEMA, registry=REGISTRY)


def test_success_flow():
    samples = [
        {
            "StartAt": "StartState",
            "States": {
                "StartState": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "End": True,
                }
            },
        },
        {
            "StartAt": "StartState",
            "States": {
                "StartState": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "Next": "NextState",
                },
                "NextState": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "End": True,
                },
            },
        },
        {
            "StartAt": "StartState",
            "States": {
                "StartState": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "End": True,
                }
            },
        },
        {
            "Comment": "Historical Data Store (HDS)",
            "StartAt": "Packages Evaluation",
            "States": {
                "Packages Evaluation": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "Next": "Process Packages",
                },
                "Process Packages": {
                    "Type": "Map",
                    "InputPath": "$",
                    "ItemsPath": "$.executions",
                    "End": True,
                    "ItemProcessor": {
                        "StartAt": "Execute Package",
                        "States": {
                            "Execute Package": {
                                "Type": "Task",
                                "Function": {"Name": "function_name", "Version": 30},
                                "End": True,
                            }
                        },
                    },
                },
            },
        },
        {
            "Comment": "Error management",
            "StartAt": "Normalize Error Event",
            "States": {
                "Normalize Error Event": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "Next": "Is Temporal Event?",
                },
                "Is Temporal Event?": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.temporal_error",
                            "boolean_equals": True,
                            "Next": "Validate Retries < 5",
                        }
                    ],
                    "Default": "Save Error",
                },
                "Validate Retries < 5": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.retries",
                            "numeric_less_than": 5,
                            "Next": "Configure Retry",
                        }
                    ],
                    "Default": "Save Error",
                },
                "Configure Retry": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "Next": "Event type?",
                },
                "Event type?": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.destination.service_type",
                            "string_equals": "lambda",
                            "Next": "Send event to lambda",
                        },
                        {
                            "Variable": "$.destination.service_type",
                            "string_equals": "sqs",
                            "Next": "Send event to SQS",
                        },
                    ],
                },
                "Send event to lambda": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "Parameters": {
                        "FunctionName.$": "$.destination.service_arn",
                        "Payload.$": "$.source_event",
                    },
                    "Next": "Delete JSON Error File Event",
                },
                "Send event to SQS": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "Parameters": {
                        "QueueUrl.$": "$.destination.service_url",
                        "MessageBody.$": "$.source_event",
                    },
                    "Next": "Delete JSON Error File Event",
                },
                "Save Error": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "Parameters": {
                        "TableName": "$.DBErrorsTable",
                        "Item": {
                            "id": {"S.$": "$.error_id"},
                            "source": {"M.$": "$.source"},
                            "process": {"M.$": "$.process"},
                            "timestamp": {
                                "N.$": "States.JsonToString($.error_timestamp)"
                            },
                            "type": {"S.$": "$.error_type"},
                            "message": {"S.$": "$.error_message"},
                            "additional_info": {"S.$": "$.error_additional_info"},
                            "start_timestamp": {
                                "N.$": "States.JsonToString($.start_timestamp)"
                            },
                            "retries": {"N.$": "States.JsonToString($.retries)"},
                            "temporal_error": {"BOOL.$": "$.temporal_error"},
                        },
                    },
                    "ResultPath": "$.dynamo_output",
                    "Next": "Notify?",
                },
                "Notify?": {
                    "Type": "Choice",
                    "Choices": [
                        {
                            "Variable": "$.notify.send",
                            "boolean_equals": True,
                            "Next": "Send notification",
                        }
                    ],
                    "Default": "Delete JSON Error File Event",
                },
                "Send notification": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "Parameters": {
                        "notification_type.$": "$.notify.notify_type",
                        "process.$": "$.process.name",
                        "step.$": "$.process.step",
                        "resource.$": "$.source.name",
                        "message.$": "$.error_message",
                        "buttons": [
                            {
                                "button_text": "View error",
                                "button_url.$": "States.Format('https://us-east-1.console.aws.amazon.com/dynamodbv2/home?region=us-east-1#edit-item?itemMode=2&pk={}&table=${DBErrorsTable}', $.error_id)",
                            }
                        ],
                    },
                    "Next": "Delete JSON Error File Event",
                },
                "Delete JSON Error File Event": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "Parameters": {
                        "Bucket.$": "$.error_file_info.bucket",
                        "Key.$": "$.error_file_info.key",
                    },
                    "End": True,
                },
            },
        },
    ]

    assert all(VALIDATOR.is_valid(data) for data in samples)


def test_fail_flow():
    samples = [
        {
            "States": {
                "StartState": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "Next": "NextState",
                },
                "NextState": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "End": True,
                },
            },
            "End": True,
        },
        {
            "StartAt": "StartState",
        },
        {
            "StartAt": "StartState",
            "States": {
                "StartState": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "Next": "NextState",
                    "End": True,
                },
                "NextState": {
                    "Type": "Task",
                    "Function": {"Name": "function_name"},
                    "End": True,
                    "Next": "NextState",
                },
            },
            "End": True,
        },
    ]

    assert all(not VALIDATOR.is_valid(data) for data in samples)
