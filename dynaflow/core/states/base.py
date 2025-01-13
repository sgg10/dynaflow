import time
from typing import Any, Dict, Union

from dynaflow.core import constants as c
from dynaflow.utils.data_manipulation import (
    apply_input_path,
    apply_parameters,
    apply_result_path,
    apply_result_selector,
    apply_output_path,
)
from dynaflow.core.states.exceptions import CatchStateError


class BaseState:
    """Base class for all flow execution states.


    Attributes:
        state_name (str): The name of the state.
        next_state (str): The name of the next state to transition to.
        end_state (bool): Flag indicating if this is a terminal state.

    Methods:
        __init__(state_definition: Dict[str, Any], enable_input_path: bool = False, enable_parameters: bool = False, enable_result_selector: bool = False, enable_result_path: bool = False, enable_output_path: bool = False) -> None:
            Initialize a base state with the given state definition.

        execute(data: Any) -> Any:
            Execute the state's logic with the given input data.

        _process(data: Any) -> Any:
            Process the input data according to state-specific logic. This is an abstract method that must be implemented by subclasses.

        is_terminal() -> bool:
            Check if this is a terminal state.

        get_next_state() -> Union[str, None]:
            Get the name of the next state to transition to.
    """

    def __init__(
        self,
        state_definition: Dict[str, Any],
        enable_input_path: bool = False,
        enable_parameters: bool = False,
        enable_result_selector: bool = False,
        enable_result_path: bool = False,
        enable_output_path: bool = False,
    ) -> None:
        """Initialize a base state with the given state definition.

        Args:
            state_definition (Dict[str, Any]): Dictionary containing the state configuration.
            enable_input_path (bool): Flag to enable input path processing.
            enable_parameters (bool): Flag to enable parameters processing.
            enable_result_selector (bool): Flag to enable result selector processing.
            enable_result_path (bool): Flag to enable result path processing.
            enable_output_path (bool): Flag to enable output path processing.

        The state definition is stored and used to:
            - Track the next state to transition to via 'Next' field
            - Determine if this is a terminal state via 'End' field
            - Configure state-specific behavior through other fields
            - Process input/output data according to enabled transformation flags
        """
        self.state_definition = state_definition
        self.state_name: str = self.state_definition.get(c.STATE_NAME_KEY)
        self.next_state: str = self.state_definition.get(c.NEXT_STATE_KEY)
        self.end_state: bool = self.state_definition.get(c.END_STATE_KEY)

        self.enable_input_path: bool = enable_input_path
        self.enable_parameters: bool = enable_parameters
        self.enable_result_selector: bool = enable_result_selector
        self.enable_result_path: bool = enable_result_path
        self.enable_output_path: bool = enable_output_path

    def execute(self, data: Any) -> Any:
        """Execute the state's logic with the given input data.

        This method implements the standard state execution flow:
        1. Applies input path to filter/extract input data
        2. Applies parameters to transform the input
        3. Processes the data through state-specific logic
        4. Applies result selector to filter/transform the output
        5. Merges result with original input via result path
        6. Applies output path to produce final result

        Args:
            data (Any): The input data to process

        Returns:
            Any: The processed and transformed output data
        """
        input_path = (
            apply_input_path(self.state_definition.get(c.INPUT_PATH_KEY), data)
            if self.enable_input_path
            else data
        )

        parameters = (
            apply_parameters(self.state_definition.get(c.PARAMETERS_KEY), input_path)
            if self.enable_parameters
            else input_path
        )

        result = self._process(parameters)

        selected_result = (
            apply_result_selector(
                self.state_definition.get(c.RESULT_SELECTOR_KEY), result
            )
            if self.enable_result_selector
            else result
        )

        combined_result = (
            apply_result_path(
                self.state_definition.get(c.RESULT_PATH_KEY),
                input_path,
                selected_result,
            )
            if self.enable_result_path
            else selected_result
        )

        output_path = (
            apply_output_path(
                self.state_definition.get(c.OUTPUT_PATH_KEY), combined_result
            )
            if self.enable_output_path
            else combined_result
        )

        return output_path

    def _process(self, data: Any) -> Any:
        """Process the input data according to state-specific logic.

        This is an abstract method that must be implemented by subclasses
        to define their specific processing behavior.

        Args:
            data (Any): The input data to process

        Returns:
            Any: The processed result

        Raises:
            NotImplementedError: If the subclass does not implement this method
        """
        raise NotImplementedError("Subclasses must implement the _process method")

    def is_terminal(self) -> bool:
        """Check if this is a terminal state.

        A state is considered terminal if it has no next state defined
        and is explicitly marked as an end state.

        Returns:
            bool: True if this is a terminal state, False otherwise
        """
        return self.end_state and self.next_state is None

    def get_next_state(self) -> Union[str, None]:
        """Get the name of the next state to transition to.

        Returns:
            Union[str, None]: The name of the next state, or None if this is a terminal state
        """
        return self.next_state


class BaseStateWithErrorHandling(BaseState):
    """

    BaseStateWithErrorHandling class extends the BaseState class to
    include error handling mechanisms such as retry and catch configurations.


    Methods:
        __init__(state_definition: Dict[str, Any]):

        _handle_catch(error_name: str, error: Exception)

        _apply_retry_logic(error_name: str, retry_attempts: int) -> tuple

        execute(data: Any) -> Any
    """

    def __init__(self, state_definition: Dict[str, Any]):
        """
        Initialize the state with the given state definition.

        Args:
            state_definition (Dict[str, Any]): A dictionary containing the state definition.

        Attributes:
            retry_config (list): Configuration for retry behavior, extracted from the state definition.
            catch_config (list): Configuration for catch behavior, extracted from the state definition.
        """
        super().__init__(
            state_definition,
            enable_input_path=True,
            enable_parameters=True,
            enable_result_selector=True,
            enable_result_path=True,
            enable_output_path=True,
        )
        self.retry_config = state_definition.get(c.RETRY_KEY, [])
        self.catch_config = state_definition.get(c.CATCH_KEY, [])

    def _handle_catch(self, error_name, error):
        """
        Handles the catch mechanism for errors during state execution.

        This method iterates through the catch configuration to determine if the
        provided error should be caught and handled. If the error matches any of
        the specified error names in the catch configuration, a CatchStateError
        is raised with the relevant details. If no match is found, the original
        error is raised.

        Args:
            error_name (str): The name of the error to handle.
            error (Exception): The error instance to handle.

        Raises:
            CatchStateError: If the error matches any of the specified error names
                in the catch configuration.
            Exception: If the error does not match any of the specified error names
                in the catch configuration.
        """
        for catch in self.catch_config:
            _errors = catch.get("ErrorEquals", [])

            if error_name in _errors or "ALL" in _errors:
                raise CatchStateError(
                    message=str(error),
                    state_name=self.state_definition.get("Name"),
                    error=error,
                    next_state=catch["Next"],
                )

        raise error

    def _apply_retry_logic(self, error_name, retry_attempts):
        """
        Applies retry logic based on the provided error name and retry attempts.

        Args:
            error_name (str): The name of the error that occurred.
            retry_attempts (int): The number of retry attempts that have been made.

        Returns:
            tuple: A tuple containing:
                - wait_time (int): The calculated wait time before the next retry attempt.
                - max_attempts (int): The maximum number of retry attempts allowed.
        """
        for retry in self.retry_config:
            _errors = retry.get("ErrorEquals", [])
            if error_name in _errors or "ALL" in _errors:
                wait_time = retry.get("IntervalSeconds", 1) * (
                    retry.get("BackoffRate", 2) ** retry_attempts
                )
                return min(wait_time, retry.get("MaxDelaySeconds", 300)), retry.get(
                    "MaxAttempts", 3
                )
        return 0, 0

    def execute(self, data):
        """
        Executes the given data with retry logic.

        Args:
            - data (any): The data to be processed by the execute method.

        Returns:
            - any: The result of the super().execute(data) method.

        Raises:
        Exception: If an error occurs and retries are either disabled or exhausted.

        The method will retry execution based on the retry configuration provided.
        If retries are enabled, it will apply retry logic to determine the wait time
        and maximum attempts for each retry. If the maximum attempts are reached or
        retries are disabled, it will handle the exception using the _handle_catch method.
        """
        retry_attempts = 0
        enable_retries = bool(self.retry_config)

        max_global_retries = c.MAX_RETRIES if enable_retries else 0

        while retry_attempts <= max_global_retries:
            try:
                return super().execute(data)
            except Exception as error:
                error_name = error.__class__.__name__

                if enable_retries:

                    wait_time, max_attempts = self._apply_retry_logic(
                        error_name, retry_attempts
                    )
                    if retry_attempts >= max_attempts:
                        self._handle_catch(error_name, error)

                    retry_attempts += 1
                    time.sleep(wait_time)
                else:
                    self._handle_catch(error_name, error)
