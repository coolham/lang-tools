import unittest
from unittest.mock import patch, MagicMock
from services.grok_service import GrokService
from services.models import Message
from utils.config import ConfigManager
import requests
import json
import os
from dotenv import load_dotenv


class TestGrokService(unittest.TestCase):
    """测试GrokService类"""
    
    def setUp(self):
        """测试前的准备工作"""
        # 加载.env文件
        load_dotenv()
        
        self.config = ConfigManager()
        
        # 从环境变量读取配置
        self.grok_api_key = os.getenv('GROK_API_KEY')
        self.grok_base_url = os.getenv('GROK_BASE_URL', 'https://api.grok.ai')
        self.grok_model = os.getenv('GROK_MODEL', 'grok-1')
        
        if not self.grok_api_key:
            raise ValueError("未找到GROK_API_KEY环境变量，请在.env文件中设置")
            
        # 设置配置
        self.config.set_grok_api_key(self.grok_api_key)
        self.config.set_grok_base_url(self.grok_base_url)
        self.config.set_grok_model(self.grok_model)
        
        self.service = GrokService()

    def test_init(self):
        """测试初始化"""

        self.assertEqual(self.service.base_url, self.grok_base_url)
        # self.assertEqual(self.service.model, self.grok_model)
        # self.assertEqual(self.service.headers["Authorization"], f"Bearer {self.grok_api_key}")
        self.assertEqual(self.service.headers["Content-Type"], "application/json")

    @patch('requests.post')
    def test_send_message_success(self, mock_post):
        """测试成功发送消息"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "这是一个测试回复"
                }
            }]
        }
        mock_post.return_value = mock_response

        # 测试发送消息
        messages = [Message(role="user", content="你好")]
        response = self.service.send_message(messages)

        # 验证结果
        self.assertEqual(response.role, "assistant")
        self.assertEqual(response.content, "这是一个测试回复")

        # 验证请求参数
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], f"{self.grok_base_url}/v1/chat/completions")
        self.assertEqual(call_args[1]["headers"], self.service.headers)
        request_data = call_args[1]["json"]
        # self.assertEqual(request_data["model"], self.grok_model)
        self.assertEqual(request_data["messages"][0]["role"], "user")
        self.assertEqual(request_data["messages"][0]["content"][0]["text"], "你好")
        self.assertEqual(request_data["temperature"], 0.7)
        self.assertEqual(request_data["max_tokens"], 2000)

    @patch('requests.post')
    def test_send_message_with_attachments(self, mock_post):
        """测试发送带附件的消息"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{
                "message": {
                    "content": "已收到图片"
                }
            }]
        }
        mock_post.return_value = mock_response

        # 测试发送带附件的消息
        message = Message(role="user", content="请分析这张图片")
        message.attachments = [{
            "type": "image",
            "data": "base64_encoded_image_data"
        }]
        messages = [message]
        response = self.service.send_message(messages)

        # 验证结果
        self.assertEqual(response.role, "assistant")
        self.assertEqual(response.content, "已收到图片")

        # 验证请求参数
        call_args = mock_post.call_args
        request_data = call_args[1]["json"]
        self.assertEqual(len(request_data["messages"][0]["content"]), 2)
        self.assertEqual(request_data["messages"][0]["content"][0]["type"], "text")
        self.assertEqual(request_data["messages"][0]["content"][1]["type"], "image_url")
        self.assertEqual(
            request_data["messages"][0]["content"][1]["image_url"]["url"],
            "data:image/png;base64,base64_encoded_image_data"
        )

    @patch('requests.post')
    def test_send_message_api_error(self, mock_post):
        """测试API请求错误"""
        # 模拟API错误
        mock_post.side_effect = requests.exceptions.RequestException("API错误")

        # 测试发送消息
        messages = [Message(role="user", content="你好")]
        with self.assertRaises(Exception) as context:
            self.service.send_message(messages)

        # 验证错误信息
        self.assertTrue("API请求失败" in str(context.exception))

    @patch('requests.get')
    def test_get_models_success(self, mock_get):
        """测试成功获取模型列表"""
        # 模拟API响应
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [
                {"id": "grok-1"},
                {"id": "grok-2"}
            ]
        }
        mock_get.return_value = mock_response

        # 测试获取模型列表
        models = self.service.get_models()

        # 验证结果
        self.assertEqual(models, ["grok-1", "grok-2"])

        # 验证请求参数
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[0][0], f"{self.grok_base_url}/v1/models")
        self.assertEqual(call_args[1]["headers"], self.service.headers)

    @patch('requests.get')
    def test_get_models_error(self, mock_get):
        """测试获取模型列表失败"""
        # 模拟API错误
        mock_get.side_effect = Exception("获取模型列表失败")

        # 测试获取模型列表
        models = self.service.get_models()

        # 验证返回默认模型
        self.assertEqual(models, ["grok-1", "grok-2"])


if __name__ == '__main__':
    unittest.main()
