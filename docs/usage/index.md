# Usage Guide

The DynaFlow library allows users to define and execute flows through a JSON-like configuration. This guide will walk you through practical examples, covering simple sequential workflows, error handling, and advanced use cases like parallel execution and data manipulation.

## Table of Contents

- [Usage Guide](#usage-guide)
  - [Table of Contents](#table-of-contents)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Basic setup](#basic-setup)
- [Defining Flows](#defining-flows)
  - [Example Flow Structure](#example-flow-structure)
- [Executing Flows](#executing-flows)
  - [Passing Input Data](#passing-input-data)
  - [Logs and Verbosity](#logs-and-verbosity)
- [Use Function Registry as Function Database](#use-function-registry-as-function-database)
  - [Installation](#installation-1)
  - [setup](#setup)
- [Examples](#examples)


# Getting Started

## Installation

Install the library using pip:

```bash
pip install dynaflow
```

## Basic setup

```python
from dynaflow import DynaFlow
from your_module import process_data


# Define your flow (you can load it from a file or a database)
my_flow = {
    "StartAt": "Task1",
    "States": {
        "Task1": {
            "Type": "Task",
            "Function": {"Name": "process_data", "Version": 1},
            "Next": "Succeed"
        },
        "Succeed": {
            "Type": "Succeed"
        }
    }
}

# Define your function database (simple example)
function_database = {
    "process_data": process_data
}

# Define the search function
search_function = lambda db, params: db[params["Name"]]


# Initialize the executor
executor = DynaFlow(
    my_flow,
    function_database=function_database,
    search_function=search_function
)

# Execute the flow
result = executor.run({"input_key": "value"})
print(result)

```

# Defining Flows

A flow is defined as a dictionary with the following key components:

- `StartAt`: The name of the initial state.
- `States`: A dictionary of states, where each key is the state name and the value is a dictionary with the state configuration.

## Example Flow Structure

```json
{
    "StartAt": "MyTask",
    "States": {
        "MyTask": {
            "Type": "Task",
            "Function": {"Name": "add_numbers", "Version": 1},
            "Next": "WaitState"
        },
        "WaitState": {
            "Type": "Wait",
            "Seconds": 5,
            "Next": "SucceedState"
        },
        "SucceedState": {
            "Type": "Succeed"
        }
    }
}
```

# Executing Flows

## Passing Input Data

Input data is passed using the run method:

```python
result = executor.run(data={"key": "value"})
```

## Logs and Verbosity

Enable verbose logging for debugging:

```python
executor = DynaFlow(
    my_flow,
    function_database=function_database,
    search_function=search_function,
    logger_name="MyDynaFlow",
    verbose=True
)
```

# Use Function Registry as Function Database

## Installation

Install the library using pip:

```bash
pip install function_registry
```

## setup

```python
from dynaflow import DynaFlow
# from your_module import process_data
from function_registry import FunctionRegistry


# Create a function catalog
fc = FunctionRegistry()

# Register your functions
@fc.save_version("process_data", 1) # Target function to use
def process_data(data):
    return data

@fc.save_version("process_data", 2)
def process_data(data):
    return { "result": data }

# Define the search function
def search_function(db: FunctionRegistry, params):
    kwargs = {"function_name": params["Name"]}
    if "Version" in params:
        kwargs["version"] = params["Version"]
    return db.get_version(**kwargs)["function"]

# Define your flow (you can load it from a file or a database)
my_flow = {
    "StartAt": "Task1",
    "States": {
        "Task1": {
            "Type": "Task",
            "InputPath": "$.input_key",
            "Function": {"Name": "process_data", "Version": 1},
            "Next": "Succeed"
        },
        "Succeed": {
            "Type": "Succeed"
        }
    }
}

# Initialize the executor
executor = DynaFlow(
    my_flow,
    function_database=fc,
    search_function=search_function
)

# Execute the flow
result = executor.run({"input_key": "value"})
print(result)

```


# Examples

| Name | Description | File |
| ---- | ----------- | ---- |
| Simple Sequential Flow | A basic flow with sequential tasks | [simple_sequential_flow.py](./examples/simple_sequential_flow.py) |
| Choice Conditions | Using choice states to handle different paths | [choice_conditions.py](./examples/choice_conditions.py) |
| Error Handling | Handling errors and retries in a flow | [retry_and_catch.py](./examples/retry_and_catch.py) |
| Parallel Flow | Running tasks in parallel | [parallel_flow.py](./examples/parallel_flow.py) |
| Map Flow | Applying a task to multiple items in a list | [map_flow.py](./examples/map_flow.py) |
