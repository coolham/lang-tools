from abc import ABC, abstractmethod
import requests
from .models import Message
from utils.config import ConfigManager


class AIService(ABC):
    """AI服务接口定义"""
    @abstractmethod
    def send_message(self, messages: list[Message]) -> Message:
        pass

    @abstractmethod
    def get_models(self) -> list[str]:
        pass


class AIServiceImpl(AIService):
    """AI服务实现类，使用requests库发送网络请求"""
    def __init__(self):
        self.config = ConfigManager()
        self.api_key = self.config.get_openai_api_key()
        self.model = self.config.get_openai_model()
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