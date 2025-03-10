"""
管理AI提示词的配置
"""
import os
import json
from typing import Dict, Optional, Any
from utils.logger import Logger

class PromptManager:
    """提示词管理器"""
    
    def __init__(self):
        self.logger = Logger.create_logger('prompt_manager')
        # 配置文件路径设置
        self.config_dir = os.path.join(os.getcwd(), "config")
        self.default_config_file = os.path.join(self.config_dir, "prompts.json")
        self.user_config_file = os.path.join(self.config_dir, "user_prompts.json")
        self.prompts = self._load_prompts()
        self.logger.info("提示词管理器初始化完成")

    def _load_prompts(self) -> Dict[str, Dict[str, str]]:
        """加载提示词配置"""
        try:
            # 确保配置目录存在
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir)
                self.logger.info(f"创建配置目录: {self.config_dir}")
            
            # 如果用户配置文件存在，优先加载用户配置
            if os.path.exists(self.user_config_file):
                self.logger.info("加载用户自定义配置")
                with open(self.user_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # 如果默认配置文件存在，加载默认配置
            if os.path.exists(self.default_config_file):
                self.logger.info("加载默认配置")
                with open(self.default_config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 复制一份到用户配置文件
                with open(self.user_config_file, 'w', encoding='utf-8') as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                return config
            
            # 如果都不存在，创建空配置
            self.logger.warning("配置文件不存在，将创建空配置")
            return self._create_empty_config()
                
        except Exception as e:
            self.logger.error(f"加载提示词配置失败: {str(e)}")
            return self._create_empty_config()

    def _create_empty_config(self) -> Dict[str, Dict[str, str]]:
        """创建空配置"""
        try:
            empty_config = {
                "analysis": {
                    "default": "",
                    "custom": None
                },
                "summary": {
                    "default": "",
                    "custom": None
                }
            }
            
            # 保存到用户配置文件
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                json.dump(empty_config, f, ensure_ascii=False, indent=4)
                
            self.logger.info("已创建空配置")
            return empty_config
            
        except Exception as e:
            self.logger.error(f"创建空配置失败: {str(e)}")
            raise

    def save_custom_prompt(self, prompt_type: str, prompt_text: str) -> bool:
        """保存自定义提示词
        
        Args:
            prompt_type: 提示词类型 ('analysis' 或 'summary')
            prompt_text: 提示词文本
            
        Returns:
            bool: 是否保存成功
        """
        try:
            if prompt_type not in self.prompts:
                self.logger.error(f"未知的提示词类型: {prompt_type}")
                return False
                
            self.prompts[prompt_type]["custom"] = prompt_text
            
            # 保存到用户配置文件
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, ensure_ascii=False, indent=4)
                
            self.logger.info(f"已保存自定义{prompt_type}提示词")
            return True
            
        except Exception as e:
            self.logger.error(f"保存自定义提示词失败: {str(e)}")
            return False

    def reset_custom_prompt(self, prompt_type: str) -> bool:
        """重置自定义提示词
        
        Args:
            prompt_type: 提示词类型 ('analysis' 或 'summary')
            
        Returns:
            bool: 是否重置成功
        """
        try:
            if prompt_type not in self.prompts:
                self.logger.error(f"未知的提示词类型: {prompt_type}")
                return False
            
            # 从默认配置文件加载默认值
            if os.path.exists(self.default_config_file):
                with open(self.default_config_file, 'r', encoding='utf-8') as f:
                    default_config = json.load(f)
                    self.prompts[prompt_type] = default_config[prompt_type]
            else:
                self.prompts[prompt_type]["custom"] = None
            
            # 保存到用户配置文件
            with open(self.user_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, ensure_ascii=False, indent=4)
                
            self.logger.info(f"已重置{prompt_type}提示词")
            return True
            
        except Exception as e:
            self.logger.error(f"重置提示词失败: {str(e)}")
            return False

    def get_prompt(self, prompt_type: str, use_custom: bool = True) -> Optional[str]:
        """获取提示词
        
        Args:
            prompt_type: 提示词类型 ('analysis' 或 'summary')
            use_custom: 是否使用自定义提示词
            
        Returns:
            str: 提示词文本
        """
        try:
            if prompt_type not in self.prompts:
                self.logger.error(f"未知的提示词类型: {prompt_type}")
                return None
                
            prompt_config = self.prompts[prompt_type]
            
            if use_custom and prompt_config["custom"]:
                return prompt_config["custom"]
            return prompt_config["default"]
            
        except Exception as e:
            self.logger.error(f"获取提示词失败: {str(e)}")
            return None

    def get_all_prompts(self) -> Dict[str, Dict[str, Any]]:
        """获取所有提示词配置"""
        return self.prompts.copy()