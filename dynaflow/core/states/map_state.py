from .base import BaseStateWithErrorHandling


class MapState(BaseStateWithErrorHandling):
    """MapState is a class that executes the same sub-flows for multiple elements.

    This state executes the same sub-flow for each item in the input data, and returns a list of results.
    """

    def __init__(self, state_definition, function_database, search_function):
        super().__init__(state_definition)
        self.processor_flow = state_definition["ItemProcessor"]
        self.function_database = function_database
        self.search_function = search_function

    def _process(self, data): ...
