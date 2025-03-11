import unittest
import os
import json
from utils.config_manager import ConfigManager

class TestConfig(unittest.TestCase):
    def setUp(self):
        """测试前创建临时配置文件"""
        self.test_config = {
            "environment": {
                "python": {
                    "conda_path": "C:\\ProgramData\\anaconda3\\condabin",
                    "conda_env": "test_env",
                    "python_version": "3.12"
                }
            }
        }
        
        # 创建临时配置文件
        os.makedirs("test_config", exist_ok=True)
        with open("test_config/default.json", "w") as f:
            json.dump(self.test_config, f)
            
        # 初始化配置管理器
        self.config = ConfigManager("test_config")
    
    def tearDown(self):
        """测试后清理临时文件"""
        if os.path.exists("test_config"):
            for file in os.listdir("test_config"):
                os.remove(os.path.join("test_config", file))
            os.rmdir("test_config")
    
    def test_get_environment_config(self):
        """测试获取环境配置"""
        env_config = self.config.get_config()["environment"]["python"]
        self.assertEqual(env_config["conda_path"], "C:\\ProgramData\\anaconda3\\condabin")
        self.assertEqual(env_config["conda_env"], "test_env")
        self.assertEqual(env_config["python_version"], "3.12")

if __name__ == '__main__':
    unittest.main()