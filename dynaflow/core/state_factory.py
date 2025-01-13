from typing import Dict, Any

from dynaflow.core.states import *
from dynaflow.core.states.base import BaseState


class StateFactory:
    """
    Factory class for creating state objects based on state definitions.
    """

    @staticmethod
    def create_state(state_definition: Dict[str, Any], **kwargs) -> BaseState:
        """
        Creates and returns a state object based on the provided state definition.

        Args:
            state_definition (Dict[str, Any]): Dictionary containing the state definition
                with properties like Type, Resource, etc.
            **kwargs: Additional keyword arguments that are passed to the state object

        Returns:
            BaseState: An instance of the appropriate state class based on the Type.

        Raises:
            ValueError: If the state Type is not recognized/supported.
        """
        _type = state_definition.get("Type")

        if _type == "Task":
            return TaskState(state_definition, function=kwargs["function"])
        elif _type == "Choice":
            return ChoiceState(state_definition)
        elif _type == "Wait":
            return WaitState(state_definition)
        elif _type == "Succeed":
            return SucceedState(state_definition)
        elif _type == "Fail":
            return FailState(state_definition)
        elif _type == "Pass":
            return PassState(state_definition)
        elif _type == "Map":
            return MapState(
                state_definition,
                function_database=kwargs["function_database"],
                search_function=kwargs["search_function"],
            )
        elif _type == "Parallel":
            return ParallelState(
                state_definition,
                function_database=kwargs["function_database"],
                search_function=kwargs["search_function"],
            )

        raise ValueError(f"Unknown state type: {_type}")
