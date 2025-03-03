import yaml


class MasterConfig:
    _instance = None

    def __new__(cls, config_file: str):
        if cls._instance is None:
            cls._instance = super(MasterConfig, cls).__new__(cls)
            cls._instance._initialize(config_file)
        return cls._instance

    def _initialize(self, config_file: str):
        with open(config_file, 'r') as file:
            self.config_data = yaml.safe_load(file)

    def get(self, key: str, default=None):
        keys = key.split('.')
        value = self.config_data
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value
