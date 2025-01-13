import jsonschema

from dynaflow.core.schemas import REGISTRY, FLOW_SCHEMA

VALIDATOR = jsonschema.Draft7Validator(FLOW_SCHEMA, registry=REGISTRY)


def validate_flow(
    flow: dict, raise_exception: bool = False, return_errors: bool = False
):
    """
    Validates a given flow dictionary using the VALIDATOR.

    Args:
        flow (dict): The flow dictionary to be validated.
        raise_exception (bool, optional): If True, raises an exception if the flow is invalid. Defaults to False.
        return_errors (bool, optional): If True, returns a tuple with a boolean indicating validity and a list of errors. Defaults to False.

    Raises:
        ValueError: If both raise_exception and return_errors are set to True.
        Exception: If raise_exception is True and the flow is invalid.

    Returns:
        bool: True if the flow is valid and raise_exception is False.
        tuple: (bool, list) if return_errors is True, where the boolean indicates validity and the list contains validation errors.
    """

    if return_errors and raise_exception:
        raise ValueError(
            "return_errors and raise_exception cannot be True at the same time"
        )

    if raise_exception:
        VALIDATOR.validate(flow)
        return True

    result = VALIDATOR.is_valid(flow)

    if return_errors:
        return result, list(VALIDATOR.iter_errors(flow))

    return result
