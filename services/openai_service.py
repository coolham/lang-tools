from openai import OpenAI
from .models import Message
from utils.config import ConfigManager
from .ai_service import AIService


class OpenAIService(AIService):
    """使用OpenAI官方SDK实现AI服务"""
    def __init__(self):
        self.config = ConfigManager()
        self.client = OpenAI(
            api_key=self.config.get_openai_api_key(),
            base_url=self.config.get_openai_base_url()
        )
        self.model = self.config.get_openai_model()

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

            # 使用OpenAI SDK发送请求
            response = self.client.chat.completions.create(
                model=self.model,
                messages=processed_messages
            )
            
            # 处理响应
            result = response.choices[0].message
            return Message(
                role="assistant",
                content=result.content
            )
        except Exception as e:
            raise Exception(f"API调用失败: {str(e)}")

    def get_models(self) -> list[str]:
        """获取可用的模型列表"""
        try:
            models = self.client.models.list()
            return [model.id for model in models]
        except Exception as e:
            # 如果获取模型列表失败，返回默认模型
            return ["gpt-3.5-turbo", "gpt-4"] 