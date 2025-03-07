import os
from typing import Dict, Any


class VersionInfo:
    """版本信息管理类"""
    
    def __init__(self):
        self.version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'VERSION')
        self._version_info = self._load_version_info()
    
    def _load_version_info(self) -> Dict[str, Any]:
        """加载版本信息"""
        version_info = {}
        try:
            with open(self.version_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 使用exec执行文件内容，但限制在安全的命名空间中
                namespace = {}
                exec(content, namespace)
                version_info = {
                    'version': namespace.get('VERSION', 'unknown'),
                    'release_date': namespace.get('RELEASE_DATE', 'unknown'),
                    'changelog': namespace.get('CHANGELOG', ''),
                    'requirements': namespace.get('REQUIREMENTS', ''),
                    'author': namespace.get('AUTHOR', 'unknown'),
                    'email': namespace.get('EMAIL', 'unknown'),
                    'license': namespace.get('LICENSE', 'unknown')
                }
        except Exception as e:
            print(f"加载版本信息失败: {str(e)}")
            version_info = {
                'version': 'unknown',
                'release_date': 'unknown',
                'changelog': '',
                'requirements': '',
                'author': 'unknown',
                'email': 'unknown',
                'license': 'unknown'
            }
        return version_info
    
    @property
    def version(self) -> str:
        """获取版本号"""
        return self._version_info['version']
    
    @property
    def release_date(self) -> str:
        """获取发布日期"""
        return self._version_info['release_date']
    
    @property
    def changelog(self) -> str:
        """获取更新说明"""
        return self._version_info['changelog']
    
    @property
    def requirements(self) -> str:
        """获取依赖要求"""
        return self._version_info['requirements']
    
    @property
    def author(self) -> str:
        """获取作者信息"""
        return self._version_info['author']
    
    @property
    def email(self) -> str:
        """获取邮箱"""
        return self._version_info['email']
    
    @property
    def license(self) -> str:
        """获取许可证"""
        return self._version_info['license']
    
    def get_full_version_info(self) -> Dict[str, Any]:
        """获取完整的版本信息"""
        return self._version_info.copy()


# 创建全局版本信息实例
version_info = VersionInfo() 