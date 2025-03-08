from openai import OpenAI
import httpx
from .message_types import Message
from .ai_service import AIService
from typing import List, Dict, Any, Generator, Union
from utils.config_manager import ConfigManager
from utils.logger import Logger


class GrokService(AIService):
    """Grok服务实现"""
    
    # 定义支持的模型
    SUPPORTED_MODELS = {
        "grok-1": {
            "max_tokens": 4096,
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0
        }
    }
    
    DEFAULT_MODEL = "grok-1"
    
    def __init__(self, config_manager: ConfigManager):
        """初始化Grok服务

        Args:
            config_manager: 配置管理器实例
        """
        super().__init__(config_manager)
        self.logger = Logger.create_logger('grok')
        self.default_model = self.DEFAULT_MODEL
        
        # 获取代理配置
        proxies = self.get_proxies()
        http_client = None
        
        if proxies:
            # 优先使用 HTTPS 代理
            proxy_url = proxies.get('https') or proxies.get('http')
            if proxy_url:
                self.logger.info(f"已配置代理服务器: {proxy_url}")
                proxy = httpx.Proxy(url=proxy_url)
                transport = httpx.HTTPTransport(
                    proxy=proxy,
                    verify=False  # 禁用 SSL 验证
                )
                http_client = httpx.Client(
                    transport=transport,
                    timeout=60.0
                )
        
        # 初始化OpenAI客户端
        client_kwargs = {
            "api_key": self.get_api_key(),
            "base_url": self.get_base_url() or "https://api.x.ai/v1"  # 使用默认的 API 地址
        }
        
        # 如果配置了代理，添加http_client
        if http_client:
            client_kwargs["http_client"] = http_client
            
        self.client = OpenAI(**client_kwargs)
    
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
            
            # 准备请求参数
            request_kwargs = {
                "model": model,  # 直接使用模型名称
                "messages": messages,
                "stream": stream,
                **model_config,  # 使用模型的其他配置参数
                **kwargs  # 允许覆盖默认参数
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