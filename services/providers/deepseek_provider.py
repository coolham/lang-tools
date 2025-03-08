import requests
from typing import List, Dict
from .base_provider import BaseProvider
from ..models import Message
from utils.logger import Logger


class DeepseekProvider(BaseProvider):
    """Deepseek官方API提供商"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com/v1"):
        super().__init__(api_key, base_url)
        self.logger = Logger.create_logger('deepseek_provider')
        
    def send_message(self, messages: List[Message], model: str, **kwargs) -> Message:
        try:
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            data = {
                'model': model,
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
                content=result['choices'][0]['message']['content']
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
            
            return [model['id'] for model in result['data']]
            
        except Exception as e:
            self.logger.error(f"Failed to get models: {str(e)}")
            return self.get_supported_models()
    
    def get_provider_name(self) -> str:
        return "Deepseek Official"
        
    def get_supported_models(self) -> List[str]:
        return [
            'deepseek-chat',
            'deepseek-coder',
            'deepseek-math',
            'deepseek-research'
        ] 