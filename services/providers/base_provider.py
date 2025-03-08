from abc import ABC, abstractmethod
from typing import List, Dict
from ..models import Message


class BaseProvider(ABC):
    """API提供商基类"""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        
    @abstractmethod
    def send_message(self, messages: List[Message], model: str, **kwargs) -> Message:
        """发送消息到API"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """获取支持的模型列表"""
        pass 