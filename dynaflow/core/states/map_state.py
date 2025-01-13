import dynaflow.core.constants as c
from .base import BaseStateWithErrorHandling
from dynaflow.utils.data_manipulation import apply_items_path


class MapState(BaseStateWithErrorHandling):
    """MapState is a class that executes the same sub-flows for multiple elements.

    This state executes the same sub-flow for each item in the input data, and returns a list of results.
    """

    def __init__(self, state_definition, function_database, search_function):
        super().__init__(state_definition)
        self.processor_flow = state_definition["ItemProcessor"]
        self.function_database = function_database
        self.search_function = search_function

    def _process(self, data):
        """
        Processes the given data by applying the items path and executing the processor flow on each item.

        Args:
            data (dict): The input data to be processed.

        Returns:
            list: A list of results from executing the processor flow on each item.

        Raises:
            ValueError: If the items path does not resolve to a list or tuple of items.

        Note: DynaFlow is imported inside the method to avoid circular imports.
        """
        from dynaflow.core.executor import DynaFlow

        items = apply_items_path(self.state_definition[c.ITEMS_PATH_KEY], data)

        if not isinstance(items, (list, tuple)):
            raise ValueError("Items path must resolve to a list of items.")

        executor = DynaFlow(
            self.processor_flow, self.function_database, self.search_function
        )

        return [executor.run(item) for item in items]
