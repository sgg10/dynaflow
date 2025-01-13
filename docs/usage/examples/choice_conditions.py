from dynaflow import DynaFlow

FLOW = {
    "StartAt": "ChoiceState",
    "States": {
        "ChoiceState": {
            "Type": "Choice",
            "Choices": [
                {
                    "And": [
                        {"Variable": "$.value", "numeric_greater_than": 10},
                        {"Variable": "$.value", "numeric_less_than": 20},
                    ],
                    "Next": "TaskAbove10",
                },
                {
                    "Not": {"Variable": "$.type", "string_equals": "Special"},
                    "Next": "TaskNotSpecial",
                },
            ],
            "Default": "DefaultTask",
        },
        "TaskAbove10": {
            "Type": "Task",
            "Function": {"Name": "process_large_value"},
            "Next": "SucceedState",
        },
        "TaskNotSpecial": {
            "Type": "Task",
            "Function": {"Name": "process_normal_value"},
            "Next": "SucceedState",
        },
        "DefaultTask": {
            "Type": "Task",
            "Function": {"Name": "process_default"},
            "Next": "SucceedState",
        },
        "SucceedState": {"Type": "Succeed"},
    },
}


def exec_with_simple_function_db():

    def process_large_value(**kwargs):
        print("Processing large value")

    def process_normal_value(**kwargs):
        print("Processing normal value")

    def process_default(**kwargs):
        print("Processing default")

    functions = {
        "process_large_value": process_large_value,
        "process_normal_value": process_normal_value,
        "process_default": process_default,
    }

    def search_function(db: dict, function_definition: dict):
        return db[function_definition["Name"]]

    executor = DynaFlow(FLOW, functions, search_function)

    print(executor.run({"value": 9, "type": "Special"}))  # process_default
    print(executor.run({"value": 10, "type": "Normal"}))  # process_normal_value
    print(executor.run({"value": 19, "type": "Special"}))  # process_large_value


if __name__ == "__main__":
    exec_with_simple_function_db()
