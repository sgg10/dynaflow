class CatchStateError(Exception):
    """
    Exception raised when an error occurs in a state and needs to be caught.

    Attributes:
        message (str): Description of the error.
        state_name (str): Name of the state where the error occurred.
        error (Exception): The original exception that was raised.
        next_state (str): The next state to transition to after the error is caught.

    Args:
        message (str): Description of the error.
        state_name (str): Name of the state where the error occurred.
        error (Exception): The original exception that was raised.
        next_state (str): The next state to transition to after the error is caught.
    """

    def __init__(
        self,
        message: str,
        state_name: str,
        error: Exception,
        next_state: str,
    ):
        super().__init__(message)
        self.state_name = state_name
        self.error = error
        self.next_state = next_state


class FailError(Exception):
    """
    Exception raised for errors in the flow execution state.

    Attributes:
        message (str): Explanation of the error.
        state_name (str): Name of the state where the error occurred.
        error (Exception): The original exception that caused this error.
    """

    def __init__(self, message: str, state_name: str, error: Exception):
        super().__init__(message)
        self.state_name = state_name
        self.error = error
