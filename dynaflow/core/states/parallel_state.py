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

    def _process(self, data):
        """
        Processes the given data by executing all branches in parallel with the same input data.
        Args:
            data (dict): The data to be processed.
        Returns:
            The results of all branches executed in parallel.

        Note: DynaFlow is imported inside the method to avoid circular imports.
        """
        from dynaflow.core.executor import DynaFlow

        results = []
        for branch in self.branches:
            executor = DynaFlow(branch, self.function_database, self.search_function)
            results.append(executor.run(data))

        return results
