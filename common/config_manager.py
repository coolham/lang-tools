# config_manager.py
import os
from utils.configure import MasterConfig


def get_global_config():
    root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(root_path, 'conf', 'config.yaml')
    return MasterConfig(config_path)

