from .base import BaseState


class PassState(BaseState):
    """A Pass State that simply passes its input to its output.

    This state type passes its input data to its output unmodified. While the input can
    be transformed through InputPath, Parameters, ResultPath and OutputPath fields, the
    core _process method performs no transformation.
    """

    def __init__(self, state_definition):
        """Initialize a Pass state with the given state definition.

        Args:
            state_definition (dict): Dictionary containing the state configuration
        """
        super().__init__(
            state_definition,
            enable_input_path=True,
            enable_parameters=True,
            enable_result_path=True,
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
