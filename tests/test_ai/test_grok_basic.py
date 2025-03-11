import unittest
from services.grok_service import GrokService
from services.message_types import Message
from utils.config_manager import ConfigManager
from utils.logger import Logger
import httpx
import ssl
from openai import OpenAI
from services.ai_service import AIService
from typing import List, Dict, Any, Generator, Union

"""
python -m unittest tests.test_ai.test_grok_basic.TestGrokBasic.test_simple_message -v
"""


class TestGrokBasic(unittest.TestCase):
    """Basic Grok functionality tests"""
    
    # Define available providers for testing
    PROVIDER_DIRECT = "official"
    PROVIDER_PROXY = "proxy"
    
    def setUp(self):
        self.config = ConfigManager()
        # Explicitly specify the provider to use
        self.provider_name = self.PROVIDER_DIRECT
        self.service = GrokService(self.config, provider_name=self.provider_name)
        self.logger = Logger.create_logger('grok-test')
        
        # Record service configuration
        self.logger.info("=== Grok服务配置 ===")
        self.logger.info(f"Provider: {self.provider_name}")
        self.logger.info(f"Base URL: {self.service.base_url}")
        self.logger.info(f"API Key: {self.service.api_key}")
        self.logger.info(f"Default Model: {self.service.default_model}")

    def test_initialization(self):
        """Test service initialization"""
        self.assertIsNotNone(self.service.client)
        self.assertEqual(self.service.default_model, "grok-2")
    
    def test_simple_message(self):
        """Test basic message handling"""
        message = Message(role="user", content="Hello, who are you?")
        try:
            response = self.service.send_message([message])
            
            # Change dictionary-style access to attribute access
            self.assertTrue(hasattr(response, 'choices'))
            self.assertTrue(len(response.choices) > 0)
            self.assertTrue(hasattr(response.choices[0], 'message'))
            self.assertTrue(hasattr(response.choices[0].message, 'content'))
        except Exception as e:
            error_str = str(e).lower()
            if "connection error" in error_str:
                self.skipTest(f"Network connectivity issue: {str(e)}")
            elif "incorrect api key" in error_str or "invalid api key" in error_str:
                self.skipTest(f"API key authentication error: {str(e)}")
            else:
                raise
        
    def test_basic_streaming(self):
        """Test basic streaming functionality"""
        message = Message(role="user", content="Count from 1 to 5")
        stream = self.service.send_message([message], stream=True)
        
        content = ""
        chunk_count = 0
        for chunk in stream:
            # Extract content from the chunk's delta
            if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                content += chunk.choices[0].delta.content
                chunk_count += 1
                self.logger.info(f"Received content: {chunk.choices[0].delta.content}")
        
        self.assertTrue(chunk_count > 0)
        self.assertTrue(len(content) > 0)
        self.logger.info(f"Complete content: {content}")

    def test_basic_chat(self):
        """测试基本对话功能"""
        messages = [Message(role="user", content="你好，请用一句话介绍自己")]
        
        self.logger.info("\n=== 测试基本对话 ===")
        self.logger.info(f"发送消息: {messages[0].content}")
        
        response = self.service.send_message(messages)
        
        self.logger.info("收到响应:")
        self.logger.info(f"Response type: {type(response)}")
        # Access properties directly instead of using dict keys
        self.logger.info(f"First choice content: {response.choices[0].message.content}")
        
        self.assertIsNotNone(response)
        self.assertTrue(hasattr(response, 'choices'))
        self.assertGreater(len(response.choices), 0)
        self.assertTrue(hasattr(response.choices[0], 'message'))
        self.assertTrue(hasattr(response.choices[0].message, 'content'))
        self.assertTrue(len(response.choices[0].message.content) > 0)

    def test_streaming_response(self):
        """测试流式响应"""
        messages = [Message(role="user", content="请用20个字描述春天")]
        
        # 获取流式响应
        response = self.service.send_message(messages, stream=True)
        
        # 收集响应内容
        content = ""
        for chunk in response:
            # Extract content from the chunk's delta
            if hasattr(chunk.choices[0], 'delta') and hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content is not None:
                content += chunk.choices[0].delta.content
                self.logger.info(f"收到chunk: {chunk.choices[0].delta.content}")
    
        self.assertTrue(len(content) > 0)
        self.logger.info(f"完整响应: {content}")

    def test_get_providers(self):
        """测试获取可用的服务商列表"""
        providers = self.service.get_providers()
        self.logger.info(f"可用的服务商: {providers}")
        self.assertIn(self.PROVIDER_DIRECT, providers)
        self.assertIn("superlang", providers)


if __name__ == '__main__':
    unittest.main()