from typing import List, Dict
from .models import Message, AIService
from .providers.base_provider import BaseProvider
from .providers.deepseek_provider import DeepseekProvider
from .providers.zhipu_provider import ZhipuProvider
from .providers.siliconflow_provider import SiliconflowProvider
from utils.config_manager import ConfigManager
from utils.logger import Logger


class DeepseekService(AIService):
    """
    Deepseek服务实现类
    支持多个API提供商
    """
    
    def __init__(self, config_manager: ConfigManager, provider_name=None):
        """初始化Deepseek服务
        
        Args:
            config_manager: 配置管理器实例
            provider_name: 指定要使用的提供商名称，若为None则使用默认提供商
        """
        super().__init__(config_manager, provider_name)
        self.logger = Logger.create_logger('deepseek_service')
        
        # 初始化所有支持的提供商
        self.providers: Dict[str, BaseProvider] = {}
        self._init_providers()
        
        # 设置当前使用的提供商和模型
        self.current_provider = self.provider_name
        self.default_model = self.config.get_default_model("deepseek")
        
        if not self.providers:
            self.logger.warning("No available Deepseek providers")
            
        self.logger.info("Deepseek service initialized")

    def _init_providers(self):
        """初始化所有配置的提供商"""
        # Deepseek官方API
        if api_key := self.config.get('deepseek_api_key'):
            self.providers["Deepseek Official"] = DeepseekProvider(
                api_key=api_key,
                base_url=self.config.get('deepseek_base_url', 'https://api.deepseek.com/v1')
            )
            
        # 智谱API
        if api_key := self.config.get('zhipu_api_key'):
            self.providers["Zhipu AI"] = ZhipuProvider(
                api_key=api_key,
                base_url=self.config.get('zhipu_base_url', 'https://open.bigmodel.cn/api/paas/v3')
            )
            
        # Siliconflow API
        if api_key := self.config.get('siliconflow_api_key'):
            self.providers["Siliconflow"] = SiliconflowProvider(
                api_key=api_key,
                base_url=self.config.get('siliconflow_base_url', 'https://api.siliconflow.com/v1')
            )

    def send_message(self, messages: List[Message]) -> Message:
        """发送消息到当前选择的提供商"""
        if not self.providers:
            raise Exception("No available Deepseek providers")
            
        if self.current_provider not in self.providers:
            raise Exception(f"Provider {self.current_provider} not available")
            
        try:
            provider = self.providers[self.current_provider]
            return provider.send_message(messages, self.default_model)
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            raise

    def get_models(self) -> List[str]:
        """获取当前提供商支持的模型列表"""
        if not self.providers:
            return []
            
        if self.current_provider not in self.providers:
            return []
            
        try:
            provider = self.providers[self.current_provider]
            return provider.get_available_models()
            
        except Exception as e:
            self.logger.error(f"Failed to get models: {str(e)}")
            return provider.get_supported_models()
            
    def get_providers(self) -> List[str]:
        """获取可用的提供商列表"""
        return list(self.providers.keys())
        
    def set_provider(self, provider_name: str):
        """设置当前使用的提供商"""
        if provider_name not in self.providers:
            raise Exception(f"Provider {provider_name} not available")
            
        self.current_provider = provider_name
        self.logger.info(f"Switched to provider: {provider_name}")
        
        # 重新加载模型列表
        available_models = self.get_models()
        if available_models and self.default_model not in available_models:
            self.default_model = available_models[0] 