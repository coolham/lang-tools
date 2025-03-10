import requests
from typing import List, Dict
from .base_provider import BaseProvider
from ..message_types import Message
from utils.logger import Logger


class ZhipuProvider(BaseProvider):
    """智谱API提供商"""
    
    def __init__(self, api_key: str, base_url: str = "https://open.bigmodel.cn/api/paas/v3"):
        super().__init__(api_key, base_url)
        self.logger = Logger.create_logger('zhipu_provider')
        
    def send_message(self, messages: List[Message], model: str, **kwargs) -> Message:
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 转换模型名称（如果需要）
            model_name = self._convert_model_name(model)
            
            data = {
                'model': model_name,
                'messages': [msg.to_dict() for msg in messages],
                'temperature': kwargs.get('temperature', 0.7),
                'max_tokens': kwargs.get('max_tokens', 4000)
            }
            
            response = requests.post(
                f'{self.base_url}/chat/completions',
                headers=headers,
                json=data
            )
            
            response.raise_for_status()
            result = response.json()
            
            return Message(
                role="assistant",
                content=result['data']['choices'][0]['message']['content']
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send message: {str(e)}")
            raise
            
    def get_available_models(self) -> List[str]:
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'{self.base_url}/models',
                headers=headers
            )
            
            response.raise_for_status()
            result = response.json()
            
            # 转换返回的模型名称为标准格式
            return [self._convert_model_name_reverse(model['id']) 
                   for model in result['data']['models']]
            
        except Exception as e:
            self.logger.error(f"Failed to get models: {str(e)}")
            return self.get_supported_models()
    
    def get_provider_name(self) -> str:
        return "Zhipu AI"
        
    def get_supported_models(self) -> List[str]:
        return [
            'deepseek-chat',
            'deepseek-coder'
        ]
        
    def _convert_model_name(self, model: str) -> str:
        """转换模型名称为提供商特定格式"""
        model_mapping = {
            'deepseek-chat': 'zhipu-deepseek-chat',
            'deepseek-coder': 'zhipu-deepseek-coder'
        }
        return model_mapping.get(model, model)
        
    def _convert_model_name_reverse(self, model: str) -> str:
        """将提供商特定的模型名称转换为标准格式"""
        model_mapping = {
            'zhipu-deepseek-chat': 'deepseek-chat',
            'zhipu-deepseek-coder': 'deepseek-coder'
        }
        return model_mapping.get(model, model) 