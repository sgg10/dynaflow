import logging
from typing import Any, Callable, Dict, Optional, Tuple

from .state_factory import StateFactory
from dynaflow.utils.validator import validate_flow
from dynaflow.core.states.exceptions import CatchStateError


class DynaFlow:
    """DynaFlow is a class responsible for executing a defined flow of states.

    The flow is defined by a dictionary that specifies the states and their transitions.
    The DynaFlow initializes with this flow definition and optional parameters such as
    a function database and a function search function. It sets up logging based on the provided
    or default configurations and validates the flow definition.

    The main purpose of the DynaFlow is to manage the execution of the flow, starting from
    the initial state and proceeding through the states as defined by the flow until a terminal
    state is reached. It handles the execution of each state, manages errors during state execution,
    and logs the progress and any issues encountered.
    """

    def __init__(
        self,
        flow_definition: Dict[str, Any],
        function_database: Any = None,
        search_function: Callable[[Any, Dict[Any, Any]], Callable] = None,
        *args,
        **kwargs,
    ):
        """
        Initializes the DynaFlow with the given flow definition and optional parameters.

        Args:
            flow_definition (Dict[str, Any]): The definition of the flow to be executed.
            function_database (Any, optional): A database of functions. Defaults to None.
            search_function (Callable[[Any, Dict[Any, Any]], Callable], optional):
                A function to search for functions within the database. Defaults to None.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
                - logger_name (str, optional): The name of the logger. Defaults to the module's __name__.
                - logger_level (int, optional): The logging level. Defaults to logging.INFO.
                - logger_format (logging.Formatter, optional): The logging format. Defaults to None.
                - verbose (bool, optional): If True, enables verbose logging. Defaults to False.
        """
        # Set logger
        executor_logger = kwargs.get("logger")

        if executor_logger is None:
            executor_logger = logging.getLogger(kwargs.get("logger_name", __name__))
            executor_logger.setLevel(kwargs.get("logger_level", logging.INFO))
            if "logger_format" in kwargs:
                executor_logger.setFormatter(kwargs["logger_format"])

        self._executor_logger = executor_logger
        self._verbose = kwargs.get("verbose", False)

        self._make_log("Initializing DynaFlow")
        self._make_log("Validating flow definition...")

        self._validate_flow_definition(flow_definition)
        self.flow = flow_definition

        self._make_log("Flow definition is valid")

        self.functions = function_database
        self.search_function = search_function

    def _make_log(self, message: str, level: int = logging.INFO):
        """
        Logs a message with the specified logging level.

        Args:
            message (str): The message to log.
            level (int, optional): The logging level. Defaults to logging.INFO.

        Notes:
            The message will be logged if the instance is in verbose mode or if the logging level is
            greater than or equal to logging.WARNING.
        """
        if self._verbose or level >= logging.WARNING:
            self._executor_logger.log(level, message)

    def _validate_flow_definition(self, flow_definition: Dict[str, Any]):
        """
        Validates the given flow definition.

        This method checks if the provided flow definition is valid by using the
        `validate_flow` function. If the flow definition is invalid, it logs the
        errors and raises a ValueError.

        Args:
            flow_definition (Dict[str, Any]): The flow definition to be validated.

        Raises:
            ValueError: If the flow definition is invalid.
        """
        is_valid, errors = validate_flow(flow_definition, return_errors=True)

        if not is_valid:
            self._make_log("Invalid flow definition", level=logging.ERROR)
            for error in errors:
                self._make_log(str(error), level=logging.ERROR)
            raise ValueError("Invalid flow definition")

    def run(self, data: Optional[Dict[str, Any]] = {}):
        """
        Executes the flow defined in the instance.

        Args:
            data (Optional[Dict[str, Any]]): Initial data to be passed to the flow. Defaults to an empty dictionary.

        Returns:
            Dict[str, Any]: The final data after the flow execution.

        Raises:
            CatchStateError: If an error occurs during the execution of a state, it is caught and logged.

        The method follows these steps:
        1. Logs the start of the flow execution.
        2. Retrieves the states and the starting state from the flow definition.
        3. Iterates through the states until a terminal state is reached.
        4. For each state, logs the current state, creates the state instance, and executes it.
        5. If a CatchStateError is raised during state execution, it logs the error and sets the next state.
        6. Logs the completion of the flow execution and returns the final data.
        """
        self._make_log("Running flow...")

        states = self.flow["States"]
        current_state_name = self.flow["StartAt"]

        stop_flow = False

        while not stop_flow:
            self._make_log(f"Executing state {current_state_name}")

            kwargs = {
                "state_definition": {
                    **states[current_state_name],
                    "Name": current_state_name,
                },
            }
            if states[current_state_name]["Type"] == "Task":
                kwargs["function"] = self.search_function(
                    self.functions, states[current_state_name]["Function"]
                )

            if states[current_state_name]["Type"] in ("Map", "Parallel"):
                kwargs["function_database"] = self.functions
                kwargs["search_function"] = self.search_function

            state = StateFactory.create_state(**kwargs)

            try:
                data = state.execute(data)
            except CatchStateError as e:
                self._make_log(f"Caught error: {e}", level=logging.ERROR)
                state.next_state = e.next_state

            if state.is_terminal():
                stop_flow = True

            current_state_name = state.next_state

        self._make_log("Flow execution finished!")
        return data
