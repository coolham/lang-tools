import httpx
import ssl
from openai import OpenAI
from services.message_types import Message
from services.ai_service import AIService
from typing import List, Dict, Any, Generator, Union, Optional
from utils.config_manager import ConfigManager
from utils.logger import Logger

class GrokService(AIService):
    """Grok服务实现"""
    
    # 定义支持的模型
    SUPPORTED_MODELS = {
        "grok-2": {
            "temperature": 0.7,
        }
    }
    
    DEFAULT_MODEL = "grok-2"
    
    def __init__(self, config_manager: ConfigManager, provider_name=None):
        """初始化Grok服务

        Args:
            config_manager: 配置管理器实例
            provider_name: 指定要使用的提供商名称，若为None则使用默认提供商
        """
        super().__init__(config_manager, provider_name)
        self.logger = Logger.create_logger('grok')
        self.default_model = self.DEFAULT_MODEL
        
        # 获取Grok配置
        provider_config = self.config.get_provider_config("grok", self.provider_name)
        self.api_key = provider_config.get("api_key", "")
        self.base_url = provider_config.get("base_url", "https://api.x.ai/v1")
        
        # 初始化OpenAI客户端
        client_kwargs = {
            "api_key": self.api_key,
            "base_url": self.base_url
        }
        
        # 配置HTTP客户端
        http_client = self._configure_http_client(provider_config)
        if http_client:
            client_kwargs["http_client"] = http_client
        
        # Initialize OpenAI client with all prepared arguments
        self.client = OpenAI(**client_kwargs)
    
    def _configure_http_client(self, provider_config: Dict[str, Any]) -> Optional[httpx.Client]:
        """配置HTTP客户端，处理代理设置

        Args:
            provider_config: 提供商配置

        Returns:
            配置好的httpx.Client实例，如果不使用代理则返回None
        """
        # 检查是否使用代理
        use_proxy = provider_config.get("use_proxy", False)
        if not use_proxy:
            return None
            
        proxies = self.get_proxies()
        if not proxies:
            return None
            
        # 获取代理URL
        https_proxy = proxies.get('https', '')
        http_proxy = proxies.get('http', '')
        
        # 优先使用HTTP代理 (对于本地代理服务器，通常需要使用HTTP协议连接，即使目标是HTTPS)
        proxy_url = http_proxy or https_proxy
        
        if not proxy_url:
            return None
            
        # 确保proxy_url使用http://前缀 (除非代理服务器确实需要HTTPS连接)
        if not proxy_url.startswith('http://') and not proxy_url.startswith('https://'):
            proxy_url = f"http://{proxy_url}"
            
        try:
            self.logger.info(f"使用代理服务器: {proxy_url}")
            
            # 创建httpx客户端
            return httpx.Client(
                proxy=proxy_url,
                timeout=60.0,
                verify=True  # 生产环境应启用SSL验证
            )
        except Exception as e:
            self.logger.error(f"代理配置失败: {str(e)}")
            return None

    def get_model_config(self, model: str = None) -> Dict[str, Any]:
        """获取模型配置

        Args:
            model: 模型名称，如果为None则使用默认模型

        Returns:
            模型配置字典
        """
        model = model or self.default_model
        if model not in self.SUPPORTED_MODELS:
            raise ValueError(f"不支持的模型: {model}")
        return self.SUPPORTED_MODELS[model]

    def send_message(self, messages, model=None, stream=False, **kwargs):
        """发送消息到 Grok API"""
        try:
            # 获取模型配置
            model = model or self.default_model
            model_config = self.get_model_config(model)
            
            # 将 Message 对象转换为字典
            messages_dict = [
                {"role": msg.role, "content": msg.content} if isinstance(msg, Message) else msg
                for msg in messages
            ]
            
            # 准备请求参数
            request_kwargs = {
                "model": model,
                "messages": messages_dict,
                "stream": stream,
                **model_config,
                **kwargs
            }
            
            # 发送请求
            completion = self.client.chat.completions.create(**request_kwargs)
            return completion
            
        except Exception as e:
            self.logger.error(f"API请求失败: {str(e)}")
            self.logger.error(f"异常类型: {type(e)}")
            raise Exception(f"API请求失败: {str(e)}")

    def _handle_stream_response(self, stream) -> Generator:
        """处理流式响应

        Args:
            stream: OpenAI流式响应对象

        Yields:
            每个响应块的内容
        """
        try:
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            self.logger.error(f"流式响应处理失败: {str(e)}")
            raise Exception(f"流式响应处理失败: {str(e)}")

    def get_models(self) -> list[str]:
        """获取支持的模型列表"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            self.logger.error(f"获取模型列表失败: {str(e)}")
            # 如果获取失败，返回支持的模型列表
            return list(self.SUPPORTED_MODELS.keys())

    def get_providers(self) -> List[str]:
        """获取可用的提供商列表"""
        try:
            providers = self.config.get_enabled_providers("grok")
            self.logger.info(f"从配置中读取的提供商: {providers}")
            return providers
        except Exception as e:
            self.logger.error(f"获取提供商列表失败: {str(e)}")
            return []