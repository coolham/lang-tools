import os
from dotenv import load_dotenv


class ConfigManager:
    """配置管理类"""
    def __init__(self):
        # 加载.env文件
        load_dotenv()
        self.config = {
            "openai": {
                "api_key": "",
                "base_url": "https://api.openai.com",
                "model": "gpt-3.5-turbo"
            },
            "grok": {
                "api_key": "",
                "base_url": "https://api.grok.ai",
                "model": "grok-1"
            }
        }

    def get_openai_api_key(self) -> str:
        """获取OpenAI API密钥"""
        return self.config["openai"]["api_key"]

    def get_openai_model(self) -> str:
        """获取OpenAI模型名称"""
        return self.config["openai"]["model"]

    def get_openai_base_url(self) -> str:
        """获取OpenAI基础URL"""
        return self.config["openai"]["base_url"]

    def get_chat_completions_url(self) -> str:
        """获取聊天完成API的完整URL"""
        return f"{self.get_openai_base_url()}chat/completions"

    def get_grok_api_key(self) -> str:
        return self.config["grok"]["api_key"]

    def get_grok_base_url(self) -> str:
        return self.config["grok"]["base_url"]

    def get_grok_model(self) -> str:
        return self.config["grok"]["model"]

    def set_openai_api_key(self, api_key: str):
        self.config["openai"]["api_key"] = api_key

    def set_openai_base_url(self, base_url: str):
        self.config["openai"]["base_url"] = base_url

    def set_openai_model(self, model: str):
        self.config["openai"]["model"] = model

    def set_grok_api_key(self, api_key: str):
        self.config["grok"]["api_key"] = api_key

    def set_grok_base_url(self, base_url: str):
        self.config["grok"]["base_url"] = base_url

    def set_grok_model(self, model: str):
        self.config["grok"]["model"] = model 