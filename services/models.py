from datetime import datetime
from typing import List, Dict, Any


class Message:
    """消息数据模型"""
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content
        self.timestamp = datetime.now()
        self.attachments: List[Dict[str, Any]] = []

    def to_dict(self):
        data = {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
        if self.attachments:
            data["attachments"] = self.attachments
        return data

    @classmethod
    def from_dict(cls, data):
        message = cls(
            role=data["role"],
            content=data["content"]
        )
        if "attachments" in data:
            message.attachments = data["attachments"]
        return message


class ChatHistory:
    """对话历史管理"""
    def __init__(self):
        self.messages: list[Message] = []

    def add_message(self, message: Message):
        self.messages.append(message)

    def get_messages(self) -> list[Message]:
        return self.messages

    def clear(self):
        self.messages.clear() 