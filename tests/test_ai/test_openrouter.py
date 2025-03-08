import unittest
import openai
import httpx
from services.openai_service import OpenAIService
from services.message_types import Message
from utils.config_manager import ConfigManager
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

"""
执行单个测试用例：
python -m unittest tests.test_ai.test_openrouter.TestOpenRouterService.test_gpt4_specific -v
"""
class TestOpenRouterService(unittest.TestCase):
    # 定义支持的模型
    SUPPORTED_MODELS = {
        "gpt-3.5-turbo": "openai/gpt-3.5-turbo",  # 更便宜的选项
        "gpt-4o": "openai/gpt-4o",                 # 更强大的选项
        "mistral-7b": "mistralai/mistral-7b-instruct",   # 开源模型
    }
    
    # 默认测试模型
    DEFAULT_TEST_MODEL = "gpt-4o"
    
    def setUp(self):
        """测试初始化"""
        # 初始化配置管理器
        self.config = ConfigManager()
        
        # 初始化服务
        self.service = OpenAIService(self.config)
        
        # 获取服务配置
        self.provider_config = self.config.get_provider_config("openai", "openrouter")
        
        # 获取基本配置
        self.api_key = self.provider_config.get("api_key")
        self.base_url = self.provider_config.get("base_url")
        self.default_model = "gpt-4o"
        
        if not self.api_key:
            raise ValueError("未找到API密钥，请在配置文件中设置")
            
        # 打印配置信息
        logger.info("=== OpenRouter服务配置 ===")
        logger.info(f"Base URL: {self.base_url}")
        logger.info(f"API Key: {self.api_key[:8]}...")
        logger.info(f"Default Model: {self.default_model}")

    def test_init(self):
        """测试初始化"""
        self.assertEqual(self.service.get_base_url(), self.base_url)
        self.assertEqual(self.service.get_api_key(), self.api_key)

    def test_basic_chat(self):
        """测试基本对话功能"""
        messages = [Message(role="user", content="你好，请用一句话介绍自己")]
        
        logger.info("\n=== 测试基本对话 ===")
        logger.info(f"发送消息: {messages[0].content}")
        
        response = self.service.send_message(messages)
        
        logger.info("收到响应:")
        logger.info(f"Response type: {type(response)}")
        logger.info(f"Response keys: {response.keys()}")
        logger.info(f"First choice content: {response['choices'][0]['message']['content']}")
        
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
            logger.info(f"收到chunk: {chunk}")
            
        self.assertTrue(len(content) > 0)
        logger.info(f"完整响应: {content}")

    def test_system_message(self):
        """测试系统消息"""
        messages = [Message(role="user", content="你是什么类型的专家？你擅长什么？")]
        response = self.service.send_message(
            messages,
            system_message="你是一个Python编程专家，擅长算法和数据结构"
        )
        
        content = response["choices"][0]["message"]["content"]
        logger.info(f"系统消息测试响应: {content}")
        
        # 检查多个相关关键词
        keywords = ["python", "编程", "算法", "数据结构", "开发", "程序", "代码"]
        found_keywords = [word for word in keywords if word.lower() in content.lower()]
        logger.info(f"找到的关键词: {found_keywords}")
        self.assertTrue(
            len(found_keywords) > 0,
            f"响应中没有找到任何预期的关键词。响应内容: {content}"
        )

    def test_error_handling(self):
        """测试错误处理"""
        # 测试无效的API密钥
        invalid_config = ConfigManager()
        invalid_config.provider_config = {
            "openai": {
                "openrouter": {
                    "api_key": "invalid_key_12345",  # 使用明显错误的密钥
                    "base_url": self.base_url
                }
            }
        }
        
        invalid_service = OpenAIService(invalid_config)
        messages = [Message(role="user", content="测试消息")]
        
        try:
            invalid_service.send_message(messages)
            self.fail("应该抛出异常但没有")
        except Exception as e:
            error_message = str(e)
            logger.info(f"无效API密钥错误信息: {error_message}")
            self.assertTrue(
                any(term in error_message.lower() for term in 
                    ["unauthorized", "authentication", "认证失败", "invalid"])
            )

    def test_get_models(self):
        """测试获取模型列表"""
        models = self.service.get_models()
        
        self.assertIsInstance(models, list)
        self.assertTrue(len(models) > 0)
        logger.info(f"可用模型列表: {models}")

    def test_custom_parameters(self):
        """测试自定义参数"""
        custom_params = {
            "temperature": 0.9,
            "max_tokens": 50,
            "top_p": 0.8,
            "frequency_penalty": 0.2
        }
        
        messages = [Message(role="user", content="用一句话描述大海")]
        response = self.service.send_message(
            messages,
            **custom_params
        )
        
        content = response["choices"][0]["message"]["content"]
        logger.info(f"使用自定义参数的响应: {content}")
        self.assertTrue(len(content) > 0)

    def test_model_parameters(self):
        """测试模型参数配置"""
        for model_name in self.SUPPORTED_MODELS.keys():
            config = self.service.get_model_config(model_name)
            self.assertIn("max_tokens", config)
            self.assertIn("temperature", config)
            self.assertIsInstance(config["max_tokens"], int)
            self.assertIsInstance(config["temperature"], float)

    def test_gpt4_specific(self):
        """专门测试GPT-4模型的功能"""
        test_messages = [
            "分析这段Python代码的性能: for i in range(1000000): list.append(i)",
            "解释什么是P vs NP问题",
            "如何优化快速排序算法"
        ]
        
        for message_text in test_messages:
            messages = [Message(role="user", content=message_text)]
            
            response = self.service.send_message(
                messages,
                model="gpt-4o",
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response["choices"][0]["message"]["content"]
            logger.info(f"\n问题: {message_text}")
            logger.info(f"GPT-4响应: {content}")
            
            self.assertTrue(len(content) > 0)
            # 确保响应中包含技术相关的关键词
            technical_terms = ["算法", "复杂度", "优化", "性能", "时间", "空间", "O(n)", "实现"]
            self.assertTrue(any(term in content for term in technical_terms))

    def test_error_cases(self):
        """测试错误情况"""
        # 测试无效的模型名称
        messages = [Message(role="user", content="测试消息")]
        try:
            # 使用一个明显错误的模型名称
            self.service.send_message(messages, model="gpt-999-invalid-model")
            self.fail("应该抛出异常但没有")
        except Exception as e:
            error_message = str(e)
            logger.info(f"无效模型错误信息: {error_message}")
            self.assertTrue(
                any(term in error_message.lower() for term in 
                    ["model", "not found", "invalid", "not available", "not supported"])
            )

        # 测试超长输入
        # 创建一个非常长的、复杂的消息
        long_message = "这是一个测试消息，包含中文和English混合内容。" * 50000
        long_message += "还有一些特殊字符：!@#$%^&*()_+" * 1000
        messages = [Message(role="user", content=long_message)]
        
        try:
            self.service.send_message(
                messages,
                max_tokens=1,  # 使用极小的max_tokens
                model="gpt-3.5-turbo"  # 使用较便宜的模型
            )
            self.fail("应该抛出异常但没有")
        except Exception as e:
            error_message = str(e)
            logger.info(f"超长输入错误信息: {error_message}")
            self.assertTrue(
                any(term in error_message.lower() for term in 
                    ["token", "length", "too long", "超过", "exceed", "limit"])
            )

    def test_supported_models(self):
        """测试支持的模型配置"""
        for model_name, internal_name in self.SUPPORTED_MODELS.items():
            model_config = self.service.get_model_config(model_name)
            self.assertEqual(model_config["internal_name"], internal_name)
            
            # 测试每个模型是否可用
            messages = [Message(role="user", content="你好")]
            try:
                response = self.service.send_message(messages, model=model_name)
                logger.info(f"模型 {model_name} 测试成功")
                self.assertTrue(len(response["choices"][0]["message"]["content"]) > 0)
            except Exception as e:
                logger.warning(f"模型 {model_name} 测试失败: {str(e)}")
                # 如果是主要模型（gpt-3.5-turbo 或 gpt-4），则失败应该报错
                if model_name in ["gpt-3.5-turbo", "gpt-4o"]:
                    raise

if __name__ == '__main__':
    unittest.main()



