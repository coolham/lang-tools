import unittest
from services.grok_service import GrokService
from services.message_types import Message
from utils.config_manager import ConfigManager
from utils.logger import Logger



class TestGrokService(unittest.TestCase):
    """测试 Grok 服务"""
    
    DEFAULT_TEST_MODEL = "grok-1"
    
    def setUp(self):
        """测试前的准备工作"""
        self.config = ConfigManager()
            
        self.service = GrokService(self.config)
        self.logger = Logger.create_logger('grok-test')
        
        # 记录服务配置
        self.logger.info("=== Grok服务配置 ===")
        self.logger.info(f"Base URL: {self.service.base_url}")
        self.logger.info(f"API Key: {self.service.api_key}")
        self.logger.info(f"Default Model: {self.service.default_model}")

    def test_init(self):
        """测试初始化"""
        grok_config = self.config.get_provider_config("grok", "official")
        self.assertEqual(self.service.base_url, grok_config.get("base_url"))
        self.assertEqual(self.service.api_key, grok_config.get("api_key"))
        self.assertEqual(self.service.default_model, self.DEFAULT_TEST_MODEL)

    def test_basic_chat(self):
        """测试基本对话功能"""
        messages = [Message(role="user", content="你好，请用一句话介绍自己")]
        
        self.logger.info("\n=== 测试基本对话 ===")
        self.logger.info(f"发送消息: {messages[0].content}")
        
        response = self.service.send_message(messages)
        
        self.logger.info("收到响应:")
        self.logger.info(f"Response type: {type(response)}")
        self.logger.info(f"Response keys: {response.keys()}")
        self.logger.info(f"First choice content: {response['choices'][0]['message']['content']}")
        
        self.assertIsInstance(response, dict)
        self.assertIn("choices", response)
        self.assertGreater(len(response["choices"]), 0)
        self.assertIn("message", response["choices"][0])
        self.assertIn("content", response["choices"][0]["message"])
        self.assertTrue(len(response["choices"][0]["message"]["content"]) > 0)

    def test_streaming_response(self):
        """测试流式响应"""
        messages = [Message(role="user", content="请用20个字描述春天")]
        
        # 获取流式响应
        response = self.service.send_message(messages, stream=True)
        
        # 收集响应内容
        content = ""
        for chunk in response:
            content += chunk
            self.logger.info(f"收到chunk: {chunk}")
            
        self.assertTrue(len(content) > 0)
        self.logger.info(f"完整响应: {content}")

    def test_system_message(self):
        """测试系统消息"""
        messages = [
            Message(role="system", content="你是一个Python编程专家，擅长算法和数据结构"),
            Message(role="user", content="你是什么类型的专家？你擅长什么？")
        ]
        response = self.service.send_message(messages)
        
        content = response["choices"][0]["message"]["content"]
        self.logger.info(f"系统消息测试响应: {content}")
        
        # 检查多个相关关键词
        keywords = ["python", "编程", "算法", "数据结构", "开发", "程序", "代码"]
        found_keywords = [word for word in keywords if word.lower() in content.lower()]
        self.logger.info(f"找到的关键词: {found_keywords}")
        self.assertTrue(
            len(found_keywords) > 0,
            f"响应中没有找到任何预期的关键词。响应内容: {content}"
        )

    def test_error_handling(self):
        """测试错误处理"""
        # 使用无效的API密钥
        invalid_config = ConfigManager()
        grok_config = self.config.get_provider_config("grok", "official")
        invalid_config.provider_config = {
            "grok": {
                "enabled": True,
                "default_provider": "official",
                "default_model": self.DEFAULT_TEST_MODEL,
                "providers": {
                    "official": {
                        "name": "Grok Official",
                        "enabled": True,
                        "api_key": "invalid_key_12345",
                        "base_url": grok_config.get("base_url"),
                        "use_proxy": False
                    }
                }
            }
        }
        service_with_invalid_key = GrokService(invalid_config)
        
        messages = [{"role": "user", "content": "测试消息"}]
        
        try:
            service_with_invalid_key.send_message(messages)
            self.fail("应该抛出异常")
        except Exception as e:
            error_msg = str(e)
            self.logger.info(f"无效API密钥错误信息: {error_msg}")
            # 检查错误消息是否包含预期的关键词
            self.assertTrue(
                any(keyword in error_msg.lower() for keyword in 
                    ["unauthorized", "authentication", "认证", "invalid", "api_key", "error", "失败", "connection"])
            )

    def test_get_models(self):
        """测试获取模型列表"""
        models = self.service.get_models()
        
        self.assertIsInstance(models, list)
        self.assertTrue(len(models) > 0)
        self.assertIn(self.DEFAULT_TEST_MODEL, models)
        self.logger.info(f"可用模型列表: {models}")

    def test_custom_parameters(self):
        """测试自定义参数"""
        custom_params = {
            "temperature": 0.9,
            "max_tokens": 50,
            "top_p": 0.8,
            "frequency_penalty": 0.2,
            "presence_penalty": 0.2
        }
        
        messages = [Message(role="user", content="用一句话描述大海")]
        response = self.service.send_message(
            messages,
            **custom_params
        )
        
        content = response["choices"][0]["message"]["content"]
        self.logger.info(f"使用自定义参数的响应: {content}")
        self.assertTrue(len(content) > 0)

    def test_error_cases(self):
        """测试错误情况"""
        # 测试无效的模型名称
        messages = [Message(role="user", content="测试消息")]
        with self.assertRaises(ValueError) as context:
            self.service.send_message(messages, model="grok-999-invalid")
        
        error_message = str(context.exception)
        self.logger.info(f"无效模型错误信息: {error_message}")
        self.assertIn("不支持的模型", error_message)

        # 测试超长输入
        # 创建一个非常长的、复杂的消息
        long_message = "这是一个测试消息，包含中文和English混合内容。" * 50000
        long_message += "还有一些特殊字符：!@#$%^&*()_+" * 1000
        messages = [Message(role="user", content=long_message)]
        
        with self.assertRaises(Exception) as context:
            self.service.send_message(
                messages,
                max_tokens=1,  # 使用极小的max_tokens
                model=self.DEFAULT_TEST_MODEL
            )
        
        error_message = str(context.exception)
        self.logger.info(f"超长输入错误信息: {error_message}")
        self.assertTrue(
            any(term in error_message.lower() for term in 
                ["token", "length", "too long", "超过", "exceed", "limit"])
        )

    def test_supported_models(self):
        """测试支持的模型配置"""
        # 测试默认模型
        messages = [{"role": "user", "content": "你好"}]
        response = self.service.send_message(messages, model="grok-1")
        self.assertTrue(len(response["choices"][0]["message"]["content"]) > 0)

if __name__ == '__main__':
    unittest.main()
