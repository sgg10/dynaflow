from .base import BaseStateWithErrorHandling


class ParallelState(BaseStateWithErrorHandling):
    """A Parallel State that executes multiple sub-flows with the same input data.

    This state executes all defined branches and waits for all of them to complete
    before returning the results.
    """

    def __init__(self, state_definition, function_database, search_function):
        super().__init__(state_definition)
        self.branches = state_definition["Branches"]
        self.function_database = function_database
        self.search_function = search_function

    def _process(self, data): ...
