from .base import BaseStateWithErrorHandling


class TaskState(BaseStateWithErrorHandling):
    """A Task State that executes a function with retry and error handling capabilities.

    This state executes a provided function, with support for:
    - Passing input data as arguments
    """

    def __init__(self, state_definition, function):
        """Initialize a Task state with the given state definition and function.

        Args:
            state_definition (dict): Dictionary containing the state configuration
            function (callable): The function to execute in this task
        """
        super().__init__(state_definition)
        self.function = function

    def _process(self, data):
        """
        Processes the given data by calling the stored function with the data as arguments.
        Args:
            data (dict or any): The data to be processed. If the data is a dictionary,
                it will be unpacked as keyword arguments to the function.
                Otherwise, the data will be passed as a single argument.
        Returns:
            The result of the function call with the provided data.
        """

        return self.function(**data) if isinstance(data, dict) else self.function(data)
