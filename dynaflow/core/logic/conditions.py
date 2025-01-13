import re
import sys
import inspect
from types import ModuleType
from datetime import datetime
from typing import Any, Dict, List

from dynaflow.utils.data_manipulation import extract_value_by_jsonpath


CURRENT_MODULE = sys.modules[__name__]


def condition_string_equals(a: str, b: str) -> bool:
    """Returns True if both strings are equal."""
    return a == b


def condition_string_less_than(a: str, b: str) -> bool:
    """Returns True if the first string is less than the second string."""
    return a < b


def condition_string_greater_than(a: str, b: str) -> bool:
    """Returns True if the first string is greater than the second string."""
    return a > b


def condition_string_less_than_equals(a: str, b: str) -> bool:
    """Returns True if the first string is less than or equal to the second string."""
    return a <= b


def condition_string_greater_than_equals(a: str, b: str) -> bool:
    """Returns True if the first string is greater than or equal to the second string."""
    return a >= b


def condition_string_matches(a: str, pattern: str) -> bool:
    """Returns True if the string matches the given regex pattern."""
    return bool(re.match(pattern, a))


def condition_numeric_equals(a: float, b: float) -> bool:
    """Returns True if both numbers are equal."""
    return a == b


def condition_numeric_less_than(a: float, b: float) -> bool:
    """Returns True if the first number is less than the second number."""
    return a < b


def condition_numeric_greater_than(a: float, b: float) -> bool:
    """Returns True if the first number is greater than the second number."""
    return a > b


def condition_numeric_less_than_equals(a: float, b: float) -> bool:
    """Returns True if the first number is less than or equal to the second number."""
    return a <= b


def condition_numeric_greater_than_equals(a: float, b: float) -> bool:
    """Returns True if the first number is greater than or equal to the second number."""
    return a >= b


def condition_boolean_equals(a: bool, b: bool) -> bool:
    """Returns True if both booleans are equal."""
    return a == b


def condition_timestamp_equals(a: str, b: str) -> bool:
    """Returns True if both timestamps are equal."""
    return datetime.fromisoformat(a) == datetime.fromisoformat(b)


def condition_timestamp_less_than(a: str, b: str) -> bool:
    """Returns True if the first timestamp is earlier than the second timestamp."""
    return datetime.fromisoformat(a) < datetime.fromisoformat(b)


def condition_timestamp_greater_than(a: str, b: str) -> bool:
    """Returns True if the first timestamp is later than the second timestamp."""
    return datetime.fromisoformat(a) > datetime.fromisoformat(b)


def condition_timestamp_less_than_equals(a: str, b: str) -> bool:
    """Returns True if the first timestamp is earlier than or equal to the second timestamp."""
    return datetime.fromisoformat(a) <= datetime.fromisoformat(b)


def condition_timestamp_greater_than_equals(a: str, b: str) -> bool:
    """Returns True if the first timestamp is later than or equal to the second timestamp."""
    return datetime.fromisoformat(a) >= datetime.fromisoformat(b)


def condition_is_null(value: Any, expected: bool) -> bool:
    """Returns True if the value is None."""
    return (value is None) == expected


def condition_is_element_present(element: Any, collection: list) -> bool:
    """Returns True if the element is present in the collection."""
    return element in collection


def condition_is_numeric(value: Any, expected: bool) -> bool:
    """Returns True if the value is a number (int or float)."""
    return isinstance(value, (int, float)) == expected


def condition_is_string(value: Any, expected: bool) -> bool:
    """Returns True if the value is a string."""
    return isinstance(value, str) == expected


def condition_is_boolean(value: Any, expected: bool) -> bool:
    """Returns True if the value is a boolean."""
    return isinstance(value, bool) == expected


def condition_is_timestamp(value: Any, expected: bool) -> bool:
    """Returns True if the value is a valid timestamp in ISO format."""
    try:
        datetime.fromisoformat(value)
        return True == expected
    except ValueError:
        return False


# Composite conditions
def and_condition(conditions: List[Dict[str, Any]], data: Any) -> bool:
    """Returns True if all conditions in the list are True."""
    return all(evaluate_condition(condition, data) for condition in conditions)


def or_condition(conditions: List[Dict[str, Any]], data: Any) -> bool:
    """Returns True if at least one condition in the list is True."""
    return any(evaluate_condition(condition, data) for condition in conditions)


def not_condition(condition: Dict[str, Any], data: Any) -> bool:
    """Returns True if the condition is False."""
    return not evaluate_condition(condition, data)


def evaluate_condition(condition: Dict[str, Any], data: Any) -> bool:
    """
    Recursively evaluates a condition based on the specified operator and value.

    Args:
        condition (Dict[str, Any]): The condition dictionary.
        data (Any): Input data to evaluate.

    Returns:
        bool: True if the condition is met, False otherwise.
    """
    if "And" in condition:
        return and_condition(condition["And"], data)
    elif "Or" in condition:
        return or_condition(condition["Or"], data)
    elif "Not" in condition:
        return not_condition(condition["Not"], data)
    else:
        operator, value = list(
            filter(lambda x: x[0] not in ("Variable", "Next"), condition.items())
        )[0]

        operator = f"condition_{operator}"

        field = condition.get("Variable")
        if not field.startswith("$."):
            raise ValueError("Field must start with $.")

        field_value = extract_value_by_jsonpath(field, data)

        condition_function = globals().get(operator.lower())
        if not condition_function:
            raise ValueError(f"Unknown operator: {operator}")

        return condition_function(field_value, value)


def _generate_schema_for_function(func):
    """
    Generate a JSON schema for the given function's parameters.

    This function inspects the parameters of the provided function and generates
    a JSON schema that describes the expected types and required properties.

    Args:
        func (function): The function for which to generate the schema.

    Returns:
        dict: A dictionary representing the JSON schema of the function's parameters.
            The schema includes the following keys:
            - "type": Always set to "object".
            - "properties": A dictionary where each key is a parameter name and the value
                is a dictionary describing the parameter type.
            - "required": A list of parameter names that are required.
            - "additionalProperties": Set to True if the function accepts *args or **kwargs.
    """
    schema = {"type": "string"}

    sig = inspect.signature(func)

    params_to_evaluate = list(sig.parameters.items())[1:]

    if len(params_to_evaluate) == 0:
        return schema

    _, param = params_to_evaluate[0]

    if param.kind in (
        inspect.Parameter.VAR_POSITIONAL,
        inspect.Parameter.VAR_KEYWORD,
    ):
        return schema

    py_param_type = param.annotation
    param_type = ""

    if py_param_type == inspect.Parameter.empty:
        param_type = "string"
    elif py_param_type == int:
        param_type = "integer"
    elif py_param_type == float:
        param_type = "number"
    elif py_param_type == bool:
        param_type = "boolean"
    elif py_param_type in (list, tuple):
        param_type = "array"
    elif py_param_type == dict:
        param_type = "object"
    else:
        param_type = "string"

    schema["type"] = param_type

    return schema


def generate_logic_function_schemas(module: ModuleType = CURRENT_MODULE):
    """
    Generates a dictionary of schemas for functions in the given module that start with "condition_".

    Args:
        module (ModuleType, optional): The module to inspect for functions. Defaults to CURRENT_MODULE.

    Returns:
        dict: A dictionary where the keys are function names and the values are their corresponding schemas.
    """
    return [
        {
            "type": "object",
            "properties": {
                name.replace("condition_", ""): _generate_schema_for_function(obj)
            },
            "required": [name.replace("condition_", "")],
        }
        for name, obj in inspect.getmembers(module, inspect.isfunction)
        if name.startswith("condition_")
    ]
