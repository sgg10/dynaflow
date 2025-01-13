# DynaFlow Library

Welcome to the official documentation for DynaFlow, a Python library designed to simplify and enhance the execution of state-driven workflows. This document serves as the primary entry point for understanding and utilizing the library to its full potential.

## What is DynaFlow?
DynaFlow is a dynamic library that orchestrates workflows based on JSON definitions. Inspired by AWS Step Functions, it provides a robust and customizable framework for executing tasks, managing errors, and transforming data. With features like parallel execution and nested flows. This library was created as a solution to the dynamic execution of processing and validation flows that can vary depending on the clients and legal requirements that introduce or eliminate steps in ETLs. The main idea is to be able to have a flow executor and reduce the team's development time.

## Core concepts

### State-Driven Execution

Workflows are defined as a series of states. Each state represents a distinct step in the workflow and is defined by:

- Type: Specifies the state's purpose (`Task`, `Choice`, `Parallel`, etc.).
- Transitions: Determines the next state or marks the end of the workflow.
- Input/Output Management: Handles data transformations at every step.

### JSON Workflow Definitions

The workflow is defined as a JSON object, enabling clear and structured representations of even complex workflows.

Example:

```json
{
  "StartAt": "InitialTask",
  "States": {
    "InitialTask": {
      "Type": "Task",
      "Function": {"Name": "add", "Version": 1},
      "Parameters": {"a": 5, "b": 10},
      "Next": "Decision"
    },
    "Decision": {
      "Type": "Choice",
      "Choices": [
        {
          "Variable": "$.result",
          "numeric_greater_than": 10,
          "Next": "Success"
        }
      ],
      "Default": "Failure"
    },
    "Success": {
      "Type": "Succeed"
    },
    "Failure": {
      "Type": "Fail",
      "Error": "ResultTooSmall",
      "Cause": "The result was less than or equal to 10."
    }
  }
}
```

### State Types

The library supports various state types, each with unique behavior:

- **Task:** Executes a Python function dynamically resolved at runtime.
- **Choice:** Implements conditional branching.
- **Parallel:** Executes multiple branches concurrently.
- **Map:** Iterates over a collection and applies a workflow to each item.
- **Wait:** Introduces a delay (maximum an hour) before transitioning to the next state.
- **Succeed:** Marks the successful completion of a workflow.
- **Fail:** Ends the workflow with an error.
- **Pass:** Manipulates data without invoking any external functions.

### Error Handling

Built-in support for:

- **Retry:** Configurable retry policies with exponential backoff.
- **Catch:** Handles errors and defines alternative execution paths.

## Architecture Overview

DynaFlow is structured into modular components to ensure maintainability and flexibility:

1. ### Core Components
   - **Executor:** Orchestrates the execution of workflows and manages transitions between states.
   - **State Factory:** Dynamically resolves and instantiates state objects based on their type.
   - **States:** Implements the logic for each supported state type.

2. ### Utility Functions
   - **Data Manipulation:** Handles input/output transformations, including support for JSONPath.
   - **Validation:** Ensures workflow definitions adhere to the schema.

3. ### Extensibility
    DynaFlow is designed to be extensible:
    - Add custom state types by inheriting from BaseState.
    - Integrate custom function registries for dynamic function execution.

## Getting Help

- **[API Reference](api-reference/index.md):** Detailed information on classes, methods, and functions.
- **[Usage Guide](usage/index.md):** Practical examples and tutorials.
