from .base import BaseState


class SucceedState(BaseState):
    """A Succeed State that marks successful completion of a branch.

    This state type marks a branch of the state machine as successfully completed.
    It will pass its input to its output unmodified, and always end execution
    of this branch.
    """

    def __init__(self, state_definition):
        """Initialize a Succeed state with the given state definition.

        Args:
            state_definition (dict): Dictionary containing the state configuration
        """
        super().__init__(
            state_definition,
            enable_input_path=True,
            enable_output_path=True,
        )

    def _process(self, data):
        """Process the input data by passing it through unchanged.

        Args:
            data: The input data to pass through

        Returns:
            The input data unmodified
        """
        return data

    def is_terminal(self):
        """Return True to indicate this is a terminal state."""
        return True
