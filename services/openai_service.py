import httpx
from openai import OpenAI
from typing import Dict, Any, List, Generator, Union
from .ai_service import AIService
from .message_types import Message
from utils.config_manager import ConfigManager
from utils.logger import Logger
import os


class OpenAIService(AIService):
    """OpenAI服务实现"""
    
    def __init__(self, config_manager: ConfigManager):
        """初始化OpenAI服务

        Args:
            config_manager: 配置管理器实例
        """
        super().__init__(config_manager)
        self.logger = Logger.create_logger('openai')
        self.default_model = self.config.get_default_model("openai")
        
        # 获取代理配置
        proxies = self.get_proxies()
        http_client = None
        
        if proxies:
            formatted_proxies = {
                "http://": proxies.get('http', ''),
                "https://": proxies.get('https', '')
            }
            http_client = httpx.Client(
                proxies=formatted_proxies,
                transport=httpx.HTTPTransport(local_address="0.0.0.0")
            )
        
        # 初始化OpenAI客户端
        client_kwargs = {
            "api_key": self.get_api_key(),
            "base_url": self.get_base_url()
        }
        
        # 如果配置了代理，添加http_client
        if http_client:
            client_kwargs["http_client"] = http_client
        
        # 如果配置了organization_id，添加到参数中
        if "organization_id" in self.provider_config:
            client_kwargs["organization"] = self.provider_config["organization_id"]
            
        self.client = OpenAI(**client_kwargs)
    
    def send_message(self, messages: List[Message], model: str = None, **kwargs) -> Union[Dict[str, Any], Generator]:
        """发送消息到OpenAI服务

        Args:
            messages: 消息列表
            model: 模型名称
            **kwargs: 其他参数
                stream: bool, 是否使用流式响应
                max_tokens: int, 最大token数
                temperature: float, 温度参数
                system_message: str, 系统消息

        Returns:
            如果stream=True，返回一个生成器用于流式处理
            如果stream=False，返回完整的响应字典
        """
        try:
            # 获取模型配置
            model_config = self.get_model_config(model)
            
            # 准备消息列表
            message_list = []
            
            # 添加系统消息（如果提供）
            system_message = kwargs.get("system_message")
            if system_message:
                message_list.append({"role": "system", "content": system_message})
            
            # 添加用户消息
            message_list.extend([m.to_dict() for m in messages])
            
            # 准备请求参数
            request_kwargs = {
                "model": model_config["internal_name"],
                "messages": message_list,
                "stream": kwargs.get("stream", False),
                "max_tokens": kwargs.get("max_tokens", model_config.get("max_tokens", 4000)),
                "temperature": kwargs.get("temperature", model_config.get("temperature", 0.7))
            }
            
            # 添加其他可选参数
            for k, v in kwargs.items():
                if k not in ["max_tokens", "temperature", "stream", "system_message"]:
                    request_kwargs[k] = v
            
            # 发送请求
            completion = self.client.chat.completions.create(**request_kwargs)
            
            # 处理流式响应
            if kwargs.get("stream", False):
                return self._handle_stream_response(completion)
            
            # 处理普通响应
            return completion.model_dump()
            
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

    def get_models(self) -> List[str]:
        """获取支持的模型列表"""
        try:
            models = self.client.models.list()
            return [model.id for model in models.data]
        except Exception as e:
            self.logger.error(f"获取模型列表失败: {str(e)}")
            # 如果获取失败，返回配置中定义的模型
            config = self.get_model_config()
            return list(config.get("models", {}).keys()) 