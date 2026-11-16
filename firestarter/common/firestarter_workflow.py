class FirestarterWorkflow:

    def __init__(self, **kwargs) -> None:
        self._config_file = kwargs.get('config_file', None)
        self._vars = kwargs.get('vars', None)
        self._secrets = kwargs.get('secrets', None)
        self.__validate_required_vars()

    def __validate_required_vars(self):
        for var in self._required_vars():
            if not self._vars.get(var):
                raise ValueError(f"Missing required variable: {var}")

    def _required_vars(self):
        # default implementation, no required vars
        return []

    @property
    def config_file(self):
        return self._config_file

    @property
    def vars(self):
        return self._vars

    @property
    def secrets(self):
        return self._secrets

    def execute(self):
        raise NotImplementedError
