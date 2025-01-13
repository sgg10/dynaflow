from typing import Any, Dict

from .base import BaseState
from dynaflow.core.logic.conditions import evaluate_condition


class ChoiceState(BaseState):
    """
    ChoiceState is a class that represents a state in a state machine
    where the next state is determined based on a set of conditions (choices).

    The state definition includes:
    - "Choices": An optional list of choices, each containing a
        condition and the next state to transition to if the condition is met.
    - "Default": An optional default state to transition to if no choices match.


    The class processes input data to evaluate against the defined conditions
    and determines the next state accordingly. If no conditions are met and no
    default state is provided, it raises a RuntimeError.

    """

    def __init__(self, state_definition: Dict[str, Any]):
        """
        Initializes the ChoiceState with the given state definition.

        Args:
            state_definition (Dict[str, Any]): A dictionary containing the state definition.
                - "Choices" (optional): A list of choices for the state.
                - "Default" (optional): The default state to transition to if no choices match.

        Attributes:
            choices (List[Dict[str, Any]]): The list of choices for the state.
            default (Any): The default state to transition to if no choices match.
        """
        super().__init__(state_definition)
        self.choices = state_definition.get("Choices", [])
        self.default = state_definition.get("Default")

    def _process(self, data: Any) -> str:
        """
        Processes the given data and determines the next state based on the defined choices.

        Args:
            data (Any): The input data to be evaluated against the conditions.

        Returns:
            str: The input data if a condition is met or the default state is set.

        Raises:
            RuntimeError: If no condition is met and there is no default state.
        """
        for choice in self.choices:
            if evaluate_condition(choice, data):
                self.next_state = choice["Next"]
                return data

        if self.default:
            self.next_state = self.default
            return data

        raise RuntimeError("No condition was met and there is no default")
