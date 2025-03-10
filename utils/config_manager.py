import os
import json
from typing import Any, Dict, Optional, List
from utils.logger import Logger


class ConfigManager:
    """配置管理器"""
    _instance = None
    _config: Dict[str, Any] = {}
    _initialized = False
    _config_dir = None
    
    def __new__(cls, config_dir: str = None):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._config_dir = config_dir
        return cls._instance
    
    def __init__(self, config_dir: str = None):
        if not self._initialized:
            self._config_dir = config_dir or os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config')
            self._load_config()
            self._initialized = True
    
    def _get_config_paths(self) -> List[str]:
        """获取配置文件路径列表，按优先级排序"""
        return [
            os.path.join(self._config_dir, 'default.json'),  # 默认配置
            os.path.join(self._config_dir, 'local.json'),    # 本地配置（不提交到版本控制）
            os.path.join(os.path.dirname(self._config_dir), 'config.json')  # 向后兼容
        ]
    
    def is_loaded(self) -> bool:
        """检查配置是否已加载"""
        return bool(self._config)
    
    def get_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self._config.copy()
    
    def get_default_provider(self, service_name: str) -> str:
        """获取服务的默认提供商"""
        service_config = self.get_service_config(service_name)
        if not service_config:
            raise KeyError(f"Service '{service_name}' not found")
        return service_config.get("default_provider")
    
    def get_default_model(self, service_name: str) -> str:
        """获取服务的默认模型"""
        service_config = self.get_service_config(service_name)
        if not service_config:
            raise KeyError(f"Service '{service_name}' not found")
        return service_config.get("default_model")
    
    def _log_info(self, message: str):
        if not hasattr(self, 'logger'):
            self.logger = Logger.create_logger('config')
        self.logger.info(message)

    def _log_warning(self, message: str):
        if not hasattr(self, 'logger'):
            self.logger = Logger.create_logger('config')
        self.logger.warning(message)

    def _log_error(self, message: str):
        if not hasattr(self, 'logger'):
            self.logger = Logger.create_logger('config')
        self.logger.error(message)

    def _load_config(self):
        """加载配置文件"""
        try:
            # 首先加载默认配置
            config_loaded = False
            for config_path in self._get_config_paths():
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        if not config_loaded:
                            self._config = json.load(f)
                            config_loaded = True
                        else:
                            # 合并配置
                            self._merge_config(json.load(f))
            
            if not config_loaded:
                self._log_warning("No configuration files found, using default settings")
                self._create_default_config()
            
        except Exception as e:
            self._log_error(f"Failed to load configuration: {str(e)}")
            self._create_default_config()
    
    def _create_default_config(self):
        """创建默认配置"""
        self._config = {
            "ai_services": {
                "openai": {
                    "enabled": True,
                    "api_key": "",
                    "base_url": "https://api.openai.com/v1",
                    "default_model": "gpt-3.5-turbo",
                    "models": {
                        "gpt-3.5-turbo": {
                            "max_tokens": 4000,
                            "temperature": 0.7
                        }
                    }
                }
            },
            "default_service": "openai",
            "logging": {
                "level": "INFO",
                "file": "app.log"
            }
        }
        self._save_default_config()
    
    def _save_default_config(self):
        """保存默认配置"""
        try:
            # 创建配置目录
            if not os.path.exists(self._config_dir):
                os.makedirs(self._config_dir)
            
            # 保存默认配置
            default_path = os.path.join(self._config_dir, 'default.json')
            with open(default_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            self._log_info("Default configuration saved")
            
            # 创建本地配置模板
            local_path = os.path.join(self._config_dir, 'local.json')
            if not os.path.exists(local_path):
                local_config = {
                    "ai_services": {
                        "openai": {"api_key": "your-api-key-here"},
                        "deepseek": {
                            "providers": {
                                "official": {"api_key": "your-api-key-here"},
                                "zhipu": {"api_key": "your-api-key-here"},
                                "siliconflow": {"api_key": "your-api-key-here"}
                            }
                        }
                    }
                }
                with open(local_path, 'w', encoding='utf-8') as f:
                    json.dump(local_config, f, indent=4, ensure_ascii=False)
                self._log_info("Local configuration template created")
                
        except Exception as e:
            self._log_error(f"Failed to save configuration: {str(e)}")
    
    def _merge_config(self, new_config: Dict[str, Any]):
        """递归合并配置"""
        for key, value in new_config.items():
            if key in self._config:
                if isinstance(self._config[key], dict) and isinstance(value, dict):
                    self._merge_config_recursive(self._config[key], value)
                else:
                    self._config[key] = value
            else:
                self._config[key] = value
    
    def _merge_config_recursive(self, target: Dict[str, Any], source: Dict[str, Any]):
        """递归合并字典"""
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                self._merge_config_recursive(target[key], value)
            else:
                target[key] = value
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """获取指定服务的配置"""
        services = self._config.get('ai_services', {})
        if service_name not in services:
            raise KeyError(f"Service '{service_name}' not found")
        return services[service_name]
    
    def get_provider_config(self, service_name: str, provider_name: str) -> Dict[str, Any]:
        """获取指定服务提供商的配置"""
        service_config = self.get_service_config(service_name)
        providers = service_config.get('providers', {})
        if provider_name not in providers:
            raise KeyError(f"Provider '{provider_name}' not found in service '{service_name}'")
        return providers[provider_name]
    
    def get_model_config(self, service_name: str, provider_name: str, model_name: str) -> Dict[str, Any]:
        """获取指定模型的配置"""
        provider_config = self.get_provider_config(service_name, provider_name)
        models = provider_config.get('models', {})
        if model_name not in models:
            raise KeyError(f"Model '{model_name}' not found in provider '{provider_name}' of service '{service_name}'")
        return models[model_name]
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        self._config[key] = value
        self._save_default_config()
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def update(self, config: Dict[str, Any]):
        """更新配置"""
        self._merge_config(config)
        self._save_default_config()
    
    def get_enabled_services(self) -> List[str]:
        """获取已启用的服务列表"""
        services = []
        for name, config in self._config.get('ai_services', {}).items():
            if config.get('enabled', False):
                services.append(name)
        return services
    
    def get_enabled_providers(self, service_name: str) -> List[str]:
        """获取指定服务的已启用提供商列表"""
        providers = []
        service_config = self.get_service_config(service_name)
        for name, config in service_config.get('providers', {}).items():
            if config.get('enabled', False):
                providers.append(name)
        return providers 