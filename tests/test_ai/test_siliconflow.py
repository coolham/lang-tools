import unittest
from services.providers.siliconflow_provider import SiliconflowProvider
from services.models import Message
from utils.config_manager import ConfigManager
import requests
import json


class TestSiliconflowProvider(unittest.TestCase):
    """测试SiliconflowProvider类"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.config = ConfigManager()
        
        # 获取Siliconflow服务配置
        provider_config = self.config.get_provider_config("deepseek", "siliconflow")
        self.api_key = provider_config.get("api_key")
        self.base_url = provider_config.get("base_url", "https://api.siliconflow.com/v1")
        
        if not self.api_key:
            raise ValueError("未找到Siliconflow API密钥，请在配置文件中设置")
            
        self.provider = SiliconflowProvider(self.api_key, self.base_url)
        
        # 默认模型
        self.default_model = "deepseek-ai/DeepSeek-R1"

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.provider.base_url, self.base_url)
        self.assertEqual(self.provider.get_provider_name(), "Siliconflow")

    def test_send_message(self):
        """测试发送消息"""
        # 创建测试消息
        messages = [Message(role="user", content="你好，请做个自我介绍")]
        
        # 发送测试消息
        response = self.provider.send_message(messages, self.default_model)
        
        # 验证响应
        self.assertEqual(response.role, "assistant")
        self.assertIsInstance(response.content, str)
        self.assertTrue(len(response.content) > 0)

    def test_send_message_with_attachments(self):
        """测试发送带附件的消息"""
        # 创建测试消息
        message = Message(role="user", content="请分析这张图片")
        message.attachments = [{
            "type": "image",
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="  # 1x1像素的透明PNG
        }]
        messages = [message]
        
        # 发送测试消息
        response = self.provider.send_message(messages, self.default_model)

        # 验证响应
        self.assertEqual(response.role, "assistant")
        self.assertIsInstance(response.content, str)
        self.assertTrue(len(response.content) > 0)

    def test_send_message_with_code(self):
        """测试发送代码相关的消息"""
        # 创建测试消息
        messages = [Message(role="user", content="请写一个Python函数，实现冒泡排序")]
        
        # 发送测试消息
        response = self.provider.send_message(messages, self.default_model)
        
        # 验证响应
        self.assertEqual(response.role, "assistant")
        self.assertIsInstance(response.content, str)
        self.assertTrue("def" in response.content)
        self.assertTrue("sort" in response.content.lower())

    def test_send_message_with_math(self):
        """测试发送数学相关的消息"""
        # 创建测试消息
        messages = [Message(role="user", content="请解释一下泰勒展开式")]
        
        # 发送测试消息
        response = self.provider.send_message(messages, self.default_model)
        
        # 验证响应
        self.assertEqual(response.role, "assistant")
        self.assertIsInstance(response.content, str)
        self.assertTrue(len(response.content) > 100)  # 数学解释应该有一定长度

    def test_get_models(self):
        """测试获取模型列表"""
        # 获取模型列表
        models = self.provider.get_available_models()
        
        # 验证结果
        self.assertIsInstance(models, list)
        self.assertTrue(len(models) > 0)
        self.assertTrue(any("deepseek" in model for model in models))

    def test_get_supported_models(self):
        """测试获取支持的模型列表"""
        supported_models = self.provider.get_supported_models()
        self.assertIsInstance(supported_models, list)
        self.assertTrue(len(supported_models) > 0)
        self.assertTrue(any("deepseek" in model for model in supported_models))

    def test_conversation_context(self):
        """测试对话上下文"""
        # 第一条消息
        messages = [Message(role="user", content="我的名字是小明")]
        response1 = self.provider.send_message(messages, self.default_model)
        
        # 第二条消息，测试上下文记忆
        messages.append(response1)
        messages.append(Message(role="user", content="我刚才说我叫什么名字？"))
        response2 = self.provider.send_message(messages, self.default_model)
        
        # 验证响应中包含名字
        self.assertTrue("小明" in response2.content)


if __name__ == '__main__':
    unittest.main()
