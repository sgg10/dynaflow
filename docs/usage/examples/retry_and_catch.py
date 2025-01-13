from dynaflow import DynaFlow
from dynaflow.core.states.exceptions import FailError

FLOW = {
    "StartAt": "TaskWithError",
    "States": {
        "TaskWithError": {
            "Type": "Task",
            "Function": {"Name": "risky_function"},
            "Retry": [
                {"ErrorEquals": ["CustomError"], "IntervalSeconds": 1, "MaxAttempts": 3}
            ],
            "Catch": [{"ErrorEquals": ["CustomError"], "Next": "FailState"}],
            "Next": "PassState",
        },
        "PassState": {
            "Type": "Pass",
            "Next": "SucceedState",
        },
        "FailState": {
            "Type": "Fail",
            "Error": "TaskFailed",
            "Cause": "Too many retries",
        },
        "SucceedState": {"Type": "Succeed"},
    },
}


def exec_with_simple_function_db():

    class CustomError(Exception):
        pass

    def risky_function():
        raise CustomError("Something went wrong")

    functions = {"risky_function": risky_function}

    def search_function(db: dict, function_definition: dict):
        return db[function_definition["Name"]]

    executor = DynaFlow(FLOW, functions, search_function)

    try:
        print("\tFLOW_EXECUTION_RESULT:", executor.run())
    except FailError as e:
        print("\tFLOW_EXECUTION_ERROR:", e)


def exec_with_function_registry():
    from function_registry import FunctionRegistry

    fdb = FunctionRegistry()

    class CustomError(Exception):
        pass

    @fdb.save_version("risky_function", 1)
    def risky_function():
        raise CustomError("Something went wrong")

    def search_function(db: FunctionRegistry, params: dict):
        kwargs = {"function_name": params["Name"]}

        if "Version" in params:
            kwargs["version"] = params["Version"]
        return db.get_version(**kwargs)["function"]

    executor = DynaFlow(FLOW, fdb, search_function)

    try:
        print("\tFLOW_EXECUTION_RESULT:", executor.run())
    except FailError as e:
        print("\tFLOW_EXECUTION_ERROR:", e)


if __name__ == "__main__":
    print("Executing flow with simple function database:")
    exec_with_simple_function_db()
    print()
    print("Executing flow with function registry:")
    exec_with_function_registry()
