import unittest
import os
import json
from utils.config_manager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        """测试前创建临时配置文件"""
        self.test_default_config = {
            "environment": {
                "python": {
                    "conda_path": "C:\\ProgramData\\anaconda3\\condabin",
                    "conda_env": "lang1_env",
                    "python_version": "3.12"
                }
            },
            "ai_services": {
                "openai": {
                    "enabled": True,
                    "providers": {
                        "official": {
                            "name": "OpenAI Official",
                            "enabled": True,
                            "api_key": "",
                            "base_url": "https://api.openai.com/v1",
                            "models": {
                                "gpt-3.5-turbo": {
                                    "max_tokens": 4000,
                                    "temperature": 0.7
                                }
                            }
                        }
                    },
                    "default_provider": "official",
                    "default_model": "gpt-3.5-turbo"
                }
            }
        }
        
        self.test_local_config = {
            "environment": {
                "python": {
                    "conda_env": "local_test_env"
                }
            },
            "ai_services": {
                "openai": {
                    "providers": {
                        "official": {
                            "api_key": "test-api-key",
                            "organization_id": "test-org-id"
                        }
                    }
                }
            }
        }
        
        # 创建临时配置文件
        os.makedirs("test_config", exist_ok=True)
        with open("test_config/default.json", "w") as f:
            json.dump(self.test_default_config, f)
        with open("test_config/local.json", "w") as f:
            json.dump(self.test_local_config, f)
            
        # 初始化配置管理器
        self.config = ConfigManager("test_config")
    
    def tearDown(self):
        """测试后清理临时文件"""
        if os.path.exists("test_config"):
            for file in os.listdir("test_config"):
                os.remove(os.path.join("test_config", file))
            os.rmdir("test_config")
    
    def test_singleton_pattern(self):
        """测试单例模式"""
        config1 = ConfigManager("test_config")
        config2 = ConfigManager("test_config")
        self.assertIs(config1, config2)
    
    def test_load_config(self):
        """测试配置加载"""
        self.assertTrue(self.config.is_loaded())
        self.assertIn("ai_services", self.config.get_config())
    
    def test_get_service_config(self):
        """测试获取服务配置"""
        openai_config = self.config.get_service_config("openai")
        self.assertTrue(openai_config["enabled"])
        self.assertEqual(openai_config["default_provider"], "official")
    
    def test_get_provider_config(self):
        """测试获取提供商配置"""
        provider_config = self.config.get_provider_config("openai", "official")
        self.assertEqual(provider_config["name"], "OpenAI Official")
        self.assertEqual(provider_config["api_key"], "test-api-key")
        self.assertEqual(provider_config["organization_id"], "test-org-id")
    
    def test_get_model_config(self):
        """测试获取模型配置"""
        model_config = self.config.get_model_config("openai", "official", "gpt-3.5-turbo")
        self.assertEqual(model_config["max_tokens"], 4000)
        self.assertEqual(model_config["temperature"], 0.7)
    
    def test_get_default_provider(self):
        """测试获取默认提供商"""
        default_provider = self.config.get_default_provider("openai")
        self.assertEqual(default_provider, "official")
    
    def test_get_default_model(self):
        """测试获取默认模型"""
        default_model = self.config.get_default_model("openai")
        self.assertEqual(default_model, "gpt-3.5-turbo")
    
    def test_get_non_existing_service(self):
        """测试获取不存在的服务配置"""
        with self.assertRaises(KeyError):
            self.config.get_service_config("non_existing_service")
    
    def test_get_non_existing_provider(self):
        """测试获取不存在的提供商配置"""
        with self.assertRaises(KeyError):
            self.config.get_provider_config("openai", "non_existing_provider")
    
    def test_get_non_existing_model(self):
        """测试获取不存在的模型配置"""
        with self.assertRaises(KeyError):
            self.config.get_model_config("openai", "official", "non_existing_model")
    
    def test_config_override(self):
        """测试本地配置覆盖默认配置"""
        provider_config = self.config.get_provider_config("openai", "official")
        self.assertEqual(provider_config["api_key"], "test-api-key")
        self.assertEqual(provider_config["organization_id"], "test-org-id")
        self.assertEqual(provider_config["base_url"], "https://api.openai.com/v1")
    
    def test_get_environment_config(self):
        """测试获取环境配置"""
        env_config = self.config.get_config()["environment"]["python"]
        self.assertEqual(env_config["conda_path"], "C:\\ProgramData\\anaconda3\\condabin")
        self.assertEqual(env_config["conda_env"], "local_test_env")  # 本地配置覆盖默认配置
        self.assertEqual(env_config["python_version"], "3.12")
    
    def test_environment_override(self):
        """测试环境配置的覆盖机制"""
        python_config = self.config.get_config()["environment"]["python"]
        # conda_path 和 python_version 来自默认配置
        self.assertEqual(python_config["conda_path"], "C:\\ProgramData\\anaconda3\\condabin")
        self.assertEqual(python_config["python_version"], "3.12")
        # conda_env 被本地配置覆盖
        self.assertEqual(python_config["conda_env"], "local_test_env")

if __name__ == '__main__':
    unittest.main() 