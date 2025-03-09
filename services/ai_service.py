import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from utils.config_manager import ConfigManager
from .message_types import Message


class AIService(ABC):
    """AI服务基类"""
    
    def __init__(self, config_manager: ConfigManager, provider_name=None):
        """初始化AI服务基类
        
        Args:
            config_manager: 配置管理器实例
            provider_name: 指定要使用的提供商名称，若为None则使用默认提供商
        """
        self.config = config_manager
        self.service_name = self.__class__.__name__.lower().replace('service', '')
        # 使用指定的提供商，如果没有指定则使用默认提供商
        if provider_name is None:
            provider_name = self.config.get_default_provider(self.service_name)
        self.provider_name = provider_name
        self.provider_config = self.config.get_provider_config(self.service_name, self.provider_name)
        self.base_url = self.provider_config.get("base_url", "")
        self.api_key = self.provider_config.get("api_key", "")
        self.default_model = self.config.get_default_model(self.service_name)
    
    @abstractmethod
    def send_message(self, messages: List[Message], model: str = None, **kwargs) -> Dict[str, Any]:
        """发送消息到AI服务
        
        Args:
            messages: 消息列表
            model: 模型名称，如果为None则使用默认模型
            **kwargs: 其他参数，如temperature、max_tokens等
            
        Returns:
            Dict[str, Any]: API的响应数据
        """
        pass
    
    def get_model_config(self, model_name: str = None) -> Dict[str, Any]:
        """获取模型配置
        
        Args:
            model_name: 模型名称，如果为None则使用默认模型
            
        Returns:
            Dict[str, Any]: 模型配置
        """
        model_name = model_name or self.default_model
        return self.config.get_model_config(self.service_name, self.provider_name, model_name)
    
    def get_api_key(self) -> str:
        """获取API密钥"""
        return self.api_key
    
    def get_base_url(self) -> str:
        """获取基础URL"""
        return self.base_url

    def get_proxies(self) -> Optional[Dict[str, str]]:
        """获取代理配置
        
        Returns:
            Optional[Dict[str, str]]: 代理配置，如果未启用代理则返回None
        """
        if not self.provider_config.get("use_proxy", False):
            return None
            
        proxy_config = self.config.get_config().get("proxy", {})
        proxies = {}
        
        # 配置HTTP代理
        if proxy_config.get("http", {}).get("enabled", False):
            http_config = proxy_config["http"]
            auth = ""
            # 只有当用户名和密码都不为空时才添加认证信息
            if http_config.get("username") and http_config.get("password") and http_config["username"].strip() and http_config["password"].strip():
                auth = f"{http_config['username']}:{http_config['password']}@"
            proxies["http"] = f"http://{auth}{http_config['host']}:{http_config['port']}"
        
        # 配置HTTPS代理
        if proxy_config.get("https", {}).get("enabled", False):
            https_config = proxy_config["https"]
            auth = ""
            # 只有当用户名和密码都不为空时才添加认证信息
            if https_config.get("username") and https_config.get("password") and https_config["username"].strip() and https_config["password"].strip():
                auth = f"{https_config['username']}:{https_config['password']}@"
            proxies["https"] = f"https://{auth}{https_config['host']}:{https_config['port']}"
        
        return proxies if proxies else None

    @abstractmethod
    def get_models(self) -> List[str]:
        """获取支持的模型列表
        
        Returns:
            List[str]: 支持的模型列表
        """
        pass


class AIServiceImpl(AIService):
    """AI服务实现类"""
    def __init__(self, provider_name=None):
        """初始化AI服务实现
        
        Args:
            provider_name: 指定要使用的提供商名称，若为None则使用默认提供商
        """
        config_manager = ConfigManager()
        super().__init__(config_manager, provider_name)
        self.api_key = self.get_api_key()
        self.model = self.default_model
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def send_message(self, messages: list[Message]) -> Message:
        try:
            # 处理消息中的附件
            processed_messages = []
            for msg in messages:
                message_data = {
                    "role": msg.role,
                    "content": []
                }
                
                # 添加文本内容
                if msg.content:
                    message_data["content"].append({
                        "type": "text",
                        "text": msg.content
                    })
                
                # 添加附件内容
                if hasattr(msg, 'attachments') and msg.attachments:
                    for attachment in msg.attachments:
                        if attachment["type"] == "image":
                            message_data["content"].append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{attachment['data']}"
                                }
                            })
                        elif attachment["type"] == "text":
                            message_data["content"].append({
                                "type": "text",
                                "text": attachment["data"]
                            })
                
                processed_messages.append(message_data)

            response = requests.post(
                self.config.get_chat_completions_url(),
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": processed_messages
                }
            )
            response.raise_for_status()
            result = response.json()
            return Message(
                role="assistant",
                content=result["choices"][0]["message"]["content"]
            )
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")

    def get_models(self) -> list[str]:
        return ["gpt-3.5-turbo", "gpt-4"] 