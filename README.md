# DynaFlow

DynaFlow is a flexible library for executing JSON-defined workflows. Its supports dynamic state management, error handling, and data manipulation (with JSONPath), making it ideal for orchestrating complex workflows.

DynaFlow lib is ASL-based, so it shares most of its definitions. For more information about ASL, you can follow the links in the [References](#references) section.

## Features

- **State-Driven Execution:** Includes core states like `Task`, `Choice`, `Parallel`, `Map` and more.
- **Dynamic Function Handling:** Integrate with custom function registries for seamless execution.
- **Error Handling:** Built-in support for `Retry` and `Catch` rules.
- **Data Transformation:** Apply trasnformations at every stage using `InputPath`, `Parameters`, `ResultPath`, and more with JSONPath.
- **Nested Flows:** Recursive execution for `Parallel` and `Map` states.
- **JSON Validation:** Ensures flow definitions adhere to a strict schema.


## Installation

### Requirements

* Python 3.9 or higher
* pip, pipeenv or poetry

### Install with pip

```bash
pip install py-dynaflow
```

### Install from source

```bash
git clone https://github.com/sgg10/dynaflow.git
cd dynaflow
pip install -e .
```

## Quick Start

### Defining a Workflow

```json
{
    "StartAt": "GetAges",
    "States": {
        "GetAges": {
            "Type": "Pass",
            "InputPath": "$",
            "Parameters": {"ages.$": "$.users[*].age"},
            "ResultPath": "$",
            "OutputPath": "$.ages",
            "End": true,
        }
    }
}
```

### Running a Workflow

```python
from dynaflow import DynaFlow

flow = {
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
    }
}

executor = DynaFlow(
    flow,
    function_database={},
    search_function=lambda db, params: db[params["Name"]]
)
result = executor.run({"users": [{"age": 20, "name": "Alice"}, {"age": 30, "name": "Bob"}]})
print(result) # -> [20, 30]
```

## Examples

### 1. Use a custom functions

To execute flows that require functions, you can create a simple function catalog with the help of a dictionary. You must also define a search function that will search for the function in the catalog based on the parameters provided in the definition of the `Task` state.

```python
from dynaflow import DynaFlow


def get_ages(user_list: list) -> list[int]:
    return [user["age"] for user in user_list]


function_catalog = {"get_ages": get_ages}


def search_function(db, params):
    return db[params["Name"]]


flow = {
    "StartAt": "GetAges",
    "States": {
        "GetAges": {
            "Type": "Task",
            "Function": {"Name": "get_ages"},
            "Parameters": {"user_list.$": "$.users"},
            "ResultPath": "$.result",
            "End": True,
        }
    },
}

executor = DynaFlow(
    flow, function_database=function_catalog, search_function=search_function
)
result = executor.run(
    {"users": [{"age": 20, "name": "Alice"}, {"age": 30, "name": "Bob"}]}
)

print(result["result"])  # -> [20, 30]
```

### 2. Use Function Registry Library to easily manage the function catalog.

To easily manage a catalog of functions for the execution of your flows, you can install and use the [FunctionRegistry] library (https://github.com/sgg10/function-registry).

```bash
pip install function_registry
```

```python
from dynaflow import DynaFlow
from function_registry import FunctionRegistry


# Create a function catalog
fc = FunctionRegistry()

@fc.save_version("get_ages", 1)
def get_ages(user_list: list) -> list[int]:
    return [user["age"] for user in user_list]

@fc.save_version("get_ages", 2)
def get_ages(user_list: list) -> list[int]:
    return [user["age"] for user in user_list if user["age"] > 18]


def search_function(db, params):
    return db.get_version(params["Name"], params["Version"])["function"]

flow = {
    "StartAt": "GetAges",
    "States": {
        "GetAges": {
            "Type": "Task",
            "Function": {"Name": "get_ages", "Version": 2},
            "Parameters": {"user_list.$": "$.users"},
            "ResultPath": "$.result_v2",
            "Next": "GetAgesV1",
        },
        "GetAgesV1": {
            "Type": "Task",
            "Function": {"Name": "get_ages", "Version": 1},
            "Parameters": {"user_list.$": "$.users"},
            "ResultPath": "$.result_v1",
            "End": True,
        },
    },
}

executor = DynaFlow(
    flow, function_database=fc, search_function=search_function
)

result = executor.run(
    {"users": [{"age": 20, "name": "Alice"}, {"age": 30, "name": "Bob"}, {"age": 15, "name": "Charlie"}]}
)

print(result["result_v1"])  # -> [20, 30, 15]
print(result["result_v2"])  # -> [20, 30]
```

## Testing

To run the unit tests, execute the following command from the project root directory:

```bash
pytest tests
```

## Contributing

All contributions to improve Function Registry are welcome! To contribute, follow these steps:

### 1. Fork the repository

```bash
git clone https://github.com/sgg10/dynaflow.git
cd dynaflow
```

### 2. Create a new branch for your changes:

```bash
git checkout -b feature/my-feature
```

### 3. Make changes and test them locally.

### 4. Submit a pull request: Open a pull request describing your changes.

For bug reports or feature requests, please visit the [issues page](https://github.com/sgg10/dynaflow/issues)



## Documentation

For detailed information, visit the [documentation](https://github.com/sgg10/dynaflow/docs/index.md). Which includes:
- **[Usage Guide](https://github.com/sgg10/dynaflow/docs/usage/index.md):** Step-by-step examples and use cases.
- **[API Reference](https://github.com/sgg10/dynaflow/docs/api-reference/index.md):** Technical details for each module and class.


## References

- [Amazon States Language (ASL)](https://states-language.net/spec.html)
- [AWS Step Functions Docs](https://docs.aws.amazon.com/step-functions)