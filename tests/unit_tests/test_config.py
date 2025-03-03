import unittest
import os
from utils.configure import MasterConfig

class TestMasterConfig(unittest.TestCase):
    def setUp(self):
        # 创建临时配置文件用于测试
        self.config_file = 'test_config.yaml'
        with open(self.config_file, 'w') as f:
            f.write("""
app:
  name: TestApp
  version: 1.0.0
database:
  host: localhost
  port: 5432
  credentials:
    username: test_user
    password: test_pass
            """)
        # 重新初始化全局配置
        self.global_config = MasterConfig(self.config_file)
    
    def tearDown(self):
        # 清理测试文件
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
    
    def test_singleton_pattern(self):
        """测试单例模式是否正确实现"""
        config1 = self.global_config
        config2 = self.global_config
        self.assertIs(config1, config2)
    
    def test_get_existing_value(self):
        """测试获取存在的配置值"""
        self.assertEqual(self.global_config.get('app.name'), 'TestApp')
        self.assertEqual(self.global_config.get('database.port'), 5432)
        self.assertEqual(self.global_config.get('database.credentials.username'), 'test_user')
    
    def test_get_nested_value(self):
        """测试获取嵌套的配置值"""
        self.assertEqual(self.global_config.get('database.credentials.password'), 'test_pass')
    
    def test_get_non_existing_value(self):
        """测试获取不存在的配置值"""
        self.assertIsNone(self.global_config.get('non.existing.key'))
        self.assertEqual(self.global_config.get('non.existing.key', 'default'), 'default')
    
    def test_get_invalid_path(self):
        """测试无效的配置路径"""
        self.assertIsNone(self.global_config.get('app.name.invalid'))
        self.assertEqual(self.global_config.get('app.name.invalid', 'default'), 'default')

if __name__ == '__main__':
    unittest.main()