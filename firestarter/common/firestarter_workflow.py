from tasks import Tasks

class FirestarterWorkflow:
    def __init__(self, **kwargs) -> None:
        self._config_file = kwargs.get('config_file', None)
        self._vars = kwargs.get('vars', None)
        self._secrets = kwargs.get('secrets', None)

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
