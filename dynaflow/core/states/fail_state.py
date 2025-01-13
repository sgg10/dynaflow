from .base import BaseState
from .exceptions import FailError


class FailState(BaseState):
    """A Fail State that marks a branch of the state machine as failed.

    This state type marks a branch of the state machine as failed.
    It will pass its input to its output unmodified, and always end execution
    of this branch.
    """

    def __init__(self, state_definition):
        """Initialize a Fail state with the given state definition.

        Args:
            state_definition (dict): Dictionary containing the state configuration
        """
        super().__init__(state_definition)

        self.error = state_definition.get("Error")
        self.cause = state_definition.get("Cause")

    def _process(self, data):
        """
        Processes the given data and raises a FailError with a formatted error message.
        Args:
            data: The data to be processed.
        Raises:
            FailError: An error containing the formatted error message, state name, and a RuntimeError.
        """

        msg = f"[{self.error or ''}] {self.cause or ''}".strip()
        msg = f" {msg}" if msg != "[]" else msg

        raise FailError(msg, self.state_name, RuntimeError(msg))
