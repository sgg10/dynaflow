# Executor

The Flow Executor (DynaFlow) is the core engine responsible for managing and executing stateful flows defined in JSON-like formats. This executor integrates:

- Validation of flow definitions.
- Dynamic state handling using the StateFactory.
- Support for custom function resolution through an external database.
- Logging and error handling for robust execution.

It manages transitions across states, respects retry and catch mechanisms, and ensures final outputs align with user-defined configurations.

## Key Components

### `DynaFlow`

#### Constructor

```python
DynaFlow(
    flow_definition: Dict[str, Any],
    function_database: Optional[Any] = None,
    search_function: Optional[[Callable[Any, Dict[Any, Any]], Callable]] = None,
    *args,
    **kwargs
)
```

#### Parameters

- `flow_definition` (`Dict[str, Any]`): The flow definition, specifying states, transitions, and start state.

- `function_database` (`Any`, optional): A database of functions for tasks. This is user-defined.

- `search_function` (`Callable`, optional): A callable to resolve functions dynamically. Should accept:
    - Function database
    - Function name
    - Arguments
    - Metadata

- `*args` and `**kwargs`:
    - `logger` (`logging.Logger`, optional): Custom logger instance.
    - `logger_name` (`str`, optional): Custom logger name.
    - `logger_level` (`int`, optional): Logging level (default: INFO).
    - `logger_format` (`logging.Formatter`, optional): Custom logging format.
    - `verbose` (`bool`, optional): Enable verbose logging (default: False).

#### Example initialization (with simple function database)

```python

def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

functions = {
    'add': add,
    'subtract': subtract
}

def seraach_function(function_database, function_info, *args, **kwargs):
    return function_database.get(function_info['name'])

flow_definition = {...}

executor = DynaFlow(
    flow_definition=flow_definition,
    function_database=functions,
    search_function=search_function
)
```

#### Methods

`run(data: Optional[Dict[str, Any]] = {}) -> Any`

Executes the defined flow from the starting state, transitioning through each state until a terminal state is reached.

**Parameters:**

- `data` (`Dict[str, Any]`, optional): Input data for the flow.

**Returns:**

- `Any`: Output data from the flow execution.

**Example Usage**:

```python
data = {'a': 1, 'b': 2}
output = executor.run(data)
```

### `StateFactory`

#### Static Methods

`create_state(state_definition: Dict[str, Any], **kwargs)`

Generates instances of states dynamically based on their `Type`.

**Parameters:**

- `state_definition` (`Dict[str, Any]`): The state definition from the flow.
- `**kwargs`: Additional arguments to pass to the state constructor.
  - `function` (`Optional[Callable]`): Function reference for `TaskState`.
  - `function_database` (`Optional[Any]`): Database of functions for `Map/Parallel` states.
  - `search_function` (`Optional[Callable]`): Function to resolve functions dynamically.

#### Supported State Types

- `TaskState`
- `ChoiceState`
- `ParallelState`
- `MapState`
- `WaitState`
- `SucceedState`
- `FailState`
- `PassState`
