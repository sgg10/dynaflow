import re
import copy
import json
from typing import Any, Dict, List, Union

import jsonpath_ng.ext as jsonpath


def extract_value_by_jsonpath(expression: str, data: dict):
    """Retrieve value from JSON data based on a given expression.

    Args:
        expression (str): A JSONPath expression to query the data
        data (dict): The JSON/dictionary data to query from

    Returns:
        The extracted value if the expression is a direct property path,
        a list of matched values for complex queries,
        or None if no match is found

    Examples:
        ```python
        extract_value_by_jsonpath("$.a.b", {"a": {"b": 2}}) -> 2
        extract_value_by_jsonpath("$.a.b", {"a": {"b": [2, 3]}}) -> [2, 3]
        extract_value_by_jsonpath("$.a[*].b", {"a": [{"b": 2}, {"b": 3}]}) -> [2, 3]
        extract_value_by_jsonpath("$.a[*].b", {"a": [{"b": 2}, {"b": 3}, {"c": 4}]}) -> [2, 3]
        extract_value_by_jsonpath("$.a[*].b", {"a": [{"b": 2}, {"c": 3}, {"b": 4}]}) -> [2, 4]
        extract_value_by_jsonpath("$.a[*].b", {"a": [{"b": 2}, {"c": 3}, {"b": [4, 5]}]}) -> [2, [4, 5]]
        ```

    """
    result = jsonpath.parse(expression).find(data)

    if not result:
        return None

    # If the expression is a direct property path without nested searches
    if re.match(
        r"^[$a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*|\[['\"a-zA-Z0-9_-]+\])*$",
        expression,
    ):
        return result[0].value

    return [match.value for match in result]


def _split_escaped_path(path: str) -> List[str]:
    """Split a path string into parts while handling escaped dots.

    Args:
        path (str): The path string to split, which may contain escaped dots (e.g. 'a\\.b.c')

    Returns:
        List[str]: A list of path segments with escaped dots converted to regular dots
            For example: 'a\\.b.c' -> ['a.b', 'c']

    Examples:
        ```python
        _split_escaped_path("$.a.b") -> ["$", "a", "b"]
        _split_escaped_path("$.a\\.b.c") -> ["$", "a.b", "c"]
        _split_escaped_path("$.a\\.b\\.c") -> ["$", "a.b.c"]
        _split_escaped_path("$.a\\.b\\.c.d") -> ["$", "a.b.c", "d"]
        ```
    """
    # Matches dots that are not preceded by a backslash
    parts = re.split(r"(?<!\\)\.", path)
    # Remove escape characters from the keys
    return [part.replace(r"\.", ".") for part in parts]


def _apply_jsonpath_extractor(expression: str, data):
    """Apply a JSONPath expression to extract data from a dictionary.

    Args:
        expression (str): A JSONPath expression to query the data. If empty, returns original data.
        data: The JSON/dictionary data to query from

    Returns:
        The extracted value based on the expression if provided,
        otherwise returns the original data unchanged

    Examples:
        ```python
        _apply_jsonpath_extractor("$.a.b", {"a": {"b": 2}}) -> 2
        _apply_jsonpath_extractor("$.a.b", {"a": {"b": [2, 3]}}) -> [2, 3]
        _apply_jsonpath_extractor("$.a[*].b", {"a": [{"b": 2}, {"b": 3}]}) -> [2, 3]
        _apply_jsonpath_extractor("$.a[*].b", {"a": [{"b": 2}, {"b": 3}, {"c": 4}]}) -> [2, 3]
        _apply_jsonpath_extractor("$.a[*].b", {"a": [{"b": 2}, {"c": 3}, {"b": 4}]}) -> [2, 4]
        _apply_jsonpath_extractor("$.a[*].b", {"a": [{"b": 2}, {"c": 3}, {"b": [4, 5]}]}) -> [2, [4, 5]]
        ```

    """
    if expression:
        return extract_value_by_jsonpath(expression, data)
    return data


def _apply_composer(
    definition: Union[Dict, List, str, Any], data: Any
) -> Union[Dict, List, Any]:
    """Compose and transform data structures based on a definition template.

    This internal function handles the recursive transformation of data according to a definition template.
    It supports various data types and JSONPath expressions for data extraction.

    Args:
        definition: The template defining how to transform the data.
            Can be a dictionary, list, or primitive value.
        data: The source data to extract values from using JSONPath expressions.

    Returns:
        Union[dict, list, Any]: The transformed data structure based on the definition:
            - For dict definitions: Returns a new dict with transformed values
            - For list definitions: Returns a new list with transformed items
            - For string definitions starting with '$': Returns extracted value from data
            - For other types: Returns the definition value unchanged

    Examples:
        ```python
        _apply_composer({"a": "$.b"}, {"b": 2}) -> {"a": 2}
        _apply_composer({"a": {"b": "$.c"}}, {"c": 3}) -> {"a": {"b": 3}}
        _apply_composer({"a": ["$.b", "$.c"]}, {"b": 2, "c": 3}) -> {"a": [2, 3]}
        _apply_composer(["$.a", "$.b"], {"a": 2, "b": 3}) -> [2, 3]
        _apply_composer("$.a", {"a": 2}) -> 2
        _apply_composer(2, None) -> 2
        ```

    """
    if not definition:
        return data

    if not any(isinstance(definition, type) for type in (dict, list)):
        if isinstance(definition, str):
            return (
                extract_value_by_jsonpath(definition, data)
                if definition.startswith("$")
                else definition
            )
        return definition

    if isinstance(definition, list):
        result = []
        for item in definition:
            if isinstance(item, dict) or isinstance(item, list):
                result.append(_apply_composer(item, data))
            elif isinstance(item, str) and item.startswith("$"):
                result.append(extract_value_by_jsonpath(item, data))
            else:
                result.append(item)
        return result

    structured_data = {}

    for key, expr in definition.items():
        normalized_key = key[:-2] if key.endswith(".$") else key
        if isinstance(expr, dict):
            structured_data[normalized_key] = _apply_composer(expr, data)
        elif isinstance(expr, list):
            structured_data[normalized_key] = [
                _apply_composer(item, data) for item in expr
            ]
        elif isinstance(expr, str):
            structured_data[normalized_key] = (
                extract_value_by_jsonpath(expr, data) if expr.startswith("$") else expr
            )
        else:
            structured_data[normalized_key] = expr

    return structured_data


def apply_input_path(input_path: str, data):
    """Apply a JSONPath expression to extract data from a dictionary."""
    return _apply_jsonpath_extractor(input_path, data)


def apply_parameters(
    parameters: Union[Dict, List, str, Any], data: Any
) -> Union[Dict, List, Any]:
    """Transform input data according to specified parameters."""
    return _apply_composer(parameters, data)


def apply_result_selector(
    selector: Union[Dict, List, str, Any], result: Any
) -> Union[Dict, List, Any]:
    """Apply a result selector to transform the output data."""
    return _apply_composer(selector, result)


def apply_result_path(result_path, original_input, result):
    """Apply a result path to merge result data into the original input.

    Merges result data into original input at the specified JSONPath location.

    The merge is done by traversing the path parts and creating nested dictionaries
    as needed. The function properly handles keys containing dots by supporting
    both dot notation and bracket notation in JSONPath expressions.

    Example:
        For keys containing dots, use bracket notation instead of dot notation:
        $.properties['footer.navigationLinks']

        If you want to use dot notation, you must escape the dots with a backslash:
        $.properties.footer\.navigationLinks

    The function will:
    1. Copy the original input to avoid modifying it
    2. Parse and normalize the JSONPath expression
    3. Traverse the path creating nested dicts if needed
    4. Insert the result at the final location

    Args:
        result_path (str): JSONPath expression indicating where to insert the result.
            If empty, returns original input unchanged.
            If "$", returns the result directly.
        original_input (Any): Original input data to update
        result (Any): Result data to insert at the specified path

    Returns:
        Any: Updated copy of original input with result inserted at specified path
    """
    if not result_path:
        return original_input

    if not result_path.startswith("$"):
        raise ValueError(
            "Result path must start with $ to be a valid JSONPath expression"
        )

    if result_path == "$":
        return result

    result_path = re.sub(
        r"\['([^']+)'\]", lambda m: m.group(1).replace(".", r"\."), result_path
    )
    result_path = re.sub(
        r'\["([^"]+)"\]', lambda m: m.group(1).replace(".", r"\."), result_path
    )

    data_copy = copy.deepcopy(original_input)
    path_parts = _split_escaped_path(result_path)

    current = data_copy
    for _, part in enumerate(path_parts[1:-1]):  # Skip $ and last part
        if part not in current:
            current[part] = {}
        current = current[part]

    current[path_parts[-1]] = result

    return data_copy


def apply_output_path(output_path: str, data):
    """Apply a JSONPath expression to extract data from a dictionary."""
    if not output_path:
        return data

    if not output_path.startswith("$"):
        raise ValueError(
            "Output path must start with $ to be a valid JSONPath expression"
        )
    return _apply_jsonpath_extractor(output_path, data)


def apply_items_path(items_path: str, data):
    """Apply a JSONPath expression to extract iterable items from a dictionary."""
    if not items_path:
        return data

    if not items_path.startswith("$"):
        raise ValueError(
            "Items path must start with $ to be a valid JSONPath expression"
        )
    return _apply_jsonpath_extractor(items_path, data)
