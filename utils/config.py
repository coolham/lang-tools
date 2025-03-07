import os
from dotenv import load_dotenv


class ConfigManager:
    """配置管理类"""
    def __init__(self):
        # 加载.env文件
        load_dotenv()

    def get_openai_api_key(self) -> str:
        """获取OpenAI API密钥"""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("未找到OPENAI_API_KEY环境变量")
        return api_key

    def get_openai_model(self) -> str:
        """获取OpenAI模型名称"""
        model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        return model

    def get_openai_base_url(self) -> str:
        """获取OpenAI基础URL"""
        base_url = os.getenv('OPENAI_BASE_URL')
        if not base_url:
            raise ValueError("未找到OPENAI_BASE_URL环境变量")
        # 确保base_url以/结尾
        return base_url.rstrip('/') + '/'

    def get_chat_completions_url(self) -> str:
        """获取聊天完成API的完整URL"""
        return f"{self.get_openai_base_url()}chat/completions" 