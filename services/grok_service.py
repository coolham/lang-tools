from openai import OpenAI
from .models import Message
from utils.config import ConfigManager
from .ai_service import AIService
import requests
import json
from typing import List, Dict


class GrokService(AIService):
    """使用Grok API实现AI服务"""
    def __init__(self):
        self.config = ConfigManager()
        self.api_key = self.config.get_grok_api_key()
        self.base_url = self.config.get_grok_base_url()
        self.model = self.config.get_grok_model()
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def send_message(self, messages: list[Message]) -> Message:
        """发送消息到Grok API"""
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

            # 发送请求到Grok API
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers=self.headers,
                json={
                    "model": self.model,
                    "messages": processed_messages,
                    "temperature": 0.7,
                    "max_tokens": 2000
                }
            )
            
            # 检查响应状态
            response.raise_for_status()
            result = response.json()
            
            # 提取回复内容
            content = result["choices"][0]["message"]["content"]
            return Message(role="assistant", content=content)

        except requests.exceptions.RequestException as e:
            raise Exception(f"API请求失败: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"解析响应失败: {str(e)}")
        except Exception as e:
            raise Exception(f"处理消息时出错: {str(e)}")

    def get_models(self) -> list[str]:
        """获取可用的模型列表"""
        try:
            response = requests.get(
                f"{self.base_url}/v1/models",
                headers=self.headers
            )
            response.raise_for_status()
            result = response.json()
            return [model["id"] for model in result["data"]]
        except Exception as e:
            # 如果获取模型列表失败，返回默认模型
            return ["grok-1", "grok-2"] 