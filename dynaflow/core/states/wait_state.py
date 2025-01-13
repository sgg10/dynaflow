import time

from .base import BaseState
from dynaflow.utils.data_manipulation import extract_value_by_jsonpath


class WaitState(BaseState):
    """A Wait State that pauses execution for a specified duration.

    This state type introduces a delay in the state machine execution by waiting
    for a specified number of seconds before proceeding to the next state.
    The wait time must be a positive integer less than 3600 seconds (1 hour).
    """

    def __init__(self, state_definition):
        """Initialize a Wait state with the given state definition.

        Args:
            state_definition (dict): Dictionary containing the state configuration,
            must include a 'Seconds' field specifying wait duration

        Raises:
            ValueError: If Seconds field is missing, not an integer, negative, or > 3600
        """
        super().__init__(
            state_definition,
            enable_input_path=True,
            enable_output_path=True,
        )

        self.wait_time = state_definition.get("Seconds")

        if not self.wait_time:
            raise ValueError("Seconds field is required for Wait state")

    def _process(self, data):
        """Process the input data by waiting for the specified duration.

        Args:
            data: The input data to pass through

        Returns:
            The input data unmodified after waiting
        """

        if isinstance(self.wait_time, str) and self.wait_time.startswith("$."):
            self.wait_time = extract_value_by_jsonpath(self.wait_time, data)

        if not isinstance(self.wait_time, int):
            raise ValueError("Seconds field must be an integer")

        if self.wait_time < 0:
            raise ValueError("Seconds field must be a positive integer")

        if self.wait_time > 3600:
            raise ValueError("Seconds field must be less than 3600 seconds (1 hour)")

        time.sleep(self.wait_time)
        return data
