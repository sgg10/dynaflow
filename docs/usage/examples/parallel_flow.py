from dynaflow import DynaFlow

FLOW = {
    "StartAt": "ParallelState",
    "States": {
        "ParallelState": {
            "Type": "Parallel",
            "InputPath": "$",
            "ResultPath": "$.result",
            "OutputPath": "$.result",
            "Branches": [
                {
                    "StartAt": "GetAges",
                    "States": {
                        "GetAges": {
                            "Type": "Pass",
                            "InputPath": "$",
                            "Parameters": {"ages.$": "$.users[*].age"},
                            "ResultPath": "$",
                            "OutputPath": "$.ages",
                            "End": True,
                        }
                    },
                },
                {
                    "StartAt": "GetNames",
                    "States": {
                        "GetNames": {
                            "Type": "Pass",
                            "InputPath": "$",
                            "Parameters": {"names": "$.users[*].name"},
                            "ResultPath": "$",
                            "OutputPath": "$.names",
                            "End": True,
                        }
                    },
                },
            ],
            "End": True,
        }
    },
}


def exec_with_simple_function_db():

    executor = DynaFlow(FLOW, {}, lambda db, params: db[params["Name"]])

    print(
        "\tFLOW_EXECUTION_RESULT:",
        executor.run(
            {"users": [{"name": "Alice", "age": 25}, {"name": "Bob", "age": 30}]}
        ),
    )


if __name__ == "__main__":
    exec_with_simple_function_db()
