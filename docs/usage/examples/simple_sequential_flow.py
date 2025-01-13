from dynaflow import DynaFlow


FLOW = {
    "StartAt": "Task1",
    "States": {
        "Task1": {
            "Type": "Task",
            "InputPath": "$",
            "Function": {"Name": "add", "Version": 1},
            # "Parameters": {"numbers.$": "$.numbers"},
            "Parameters": {"numbers": "$.numbers"},
            "ResultPath": "$.sum_result",
            "Next": "PassState",
        },
        "PassState": {
            "Type": "Pass",
            "InputPath": "$",
            "Parameters": {"result": "$.sum_result", "nums": "$.numbers"},
            "ResultPath": "$",
            "OutputPath": "$",
            "Next": "PrintResult",
        },
        "PrintResult": {
            "Type": "Task",
            "InputPath": "$",
            "Function": {"Name": "print_components", "Version": 1},
            "Next": "SucceedState",
        },
        "SucceedState": {
            "Type": "Succeed",
            "InputPath": "$.result",
        },
    },
}


def exec_with_simple_function_db():

    def add(numbers):
        return sum(numbers)

    def print_components(**kwargs):
        for key, value in kwargs.items():
            print(f"\t{key}: {value}")

    functions = {"add": add, "print_components": print_components}

    def search_function(db: dict, function_definition: dict):
        return db[function_definition["Name"]]

    executor = DynaFlow(FLOW, functions, search_function)

    print("\tFLOW_EXECUTION_RESULT:", executor.run({"numbers": [1, 2, 3, 4, 5]}))


def exec_with_function_registry():
    from function_registry import FunctionRegistry

    fdb = FunctionRegistry()

    @fdb.save_version("add", 1)
    def add(numbers):
        return sum(numbers)

    @fdb.save_version("print_components", 1)
    def print_components(**kwargs):
        for key, value in kwargs.items():
            print(f"\t{key}: {value}")

    def search_function(db: FunctionRegistry, params: dict):
        kwargs = {"function_name": params["Name"]}

        if "Version" in params:
            kwargs["version"] = params["Version"]
        return db.get_version(**kwargs)["function"]

    executor = DynaFlow(FLOW, fdb, search_function)

    print("\tFLOW_EXECUTION_RESULT:", executor.run({"numbers": [1, 2, 3, 4, 5]}))


if __name__ == "__main__":
    print("Simple sequential  flow with simple function database")
    exec_with_simple_function_db()
    print()
    print("Simple sequential flow with function registry")
    exec_with_function_registry()
