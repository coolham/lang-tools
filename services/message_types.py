from datetime import datetime
from typing import List, Dict, Any


class Message:
    """消息数据模型"""
    def __init__(self, role: str, content: str):
        """
        初始化消息对象
        
        Args:
            role: 消息角色（user/assistant/system）
            content: 消息内容
        """
        self.role = role
        self.content = content
        self.timestamp = datetime.now()
        self.attachments: List[Dict[str, Any]] = []

    def to_dict(self) -> Dict[str, Any]:
        """
        将消息转换为字典格式
        
        Returns:
            Dict[str, Any]: 消息的字典表示
        """
        data = {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat()
        }
        if self.attachments:
            data["attachments"] = self.attachments
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """
        从字典创建消息对象
        
        Args:
            data: 消息数据字典
            
        Returns:
            Message: 新创建的消息对象
        """
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
        """初始化对话历史"""
        self.messages: List[Message] = []

    def add_message(self, message: Message) -> None:
        """
        添加消息到历史记录
        
        Args:
            message: 要添加的消息
        """
        self.messages.append(message)

    def get_messages(self) -> List[Message]:
        """
        获取所有历史消息
        
        Returns:
            List[Message]: 历史消息列表
        """
        return self.messages

    def clear(self) -> None:
        """清空历史记录"""
        self.messages.clear() 