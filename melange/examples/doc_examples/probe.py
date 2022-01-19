class Probe:
    """
    This interface is used to test asynchronous code
    """

    def can_be_measured(self) -> bool:
        raise NotImplementedError

    def sample(self) -> None:
        raise NotImplementedError
