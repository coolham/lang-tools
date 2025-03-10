import os
import json
from typing import Dict, List, Optional
from datetime import datetime

class FileIndexManager:
    """文件索引管理器，用于维护目录下所有PDF文件的唯一序号"""
    
    def __init__(self, logger):
        self.logger = logger
        self.index_file_name = "file_index.json"
        
    def generate_index(self, directory: str) -> Dict[str, dict]:
        """为目录下的所有PDF文件生成索引
        
        Args:
            directory: 目录路径
            
        Returns:
            Dict: 包含文件索引信息的字典
        """
        try:
            index_file_path = os.path.join(directory, self.index_file_name)
            
            # 如果索引文件已存在，加载它
            if os.path.exists(index_file_path):
                with open(index_file_path, 'r', encoding='utf-8') as f:
                    existing_index = json.load(f)
            else:
                existing_index = {
                    "metadata": {
                        "created_at": datetime.now().isoformat(),
                        "last_updated": datetime.now().isoformat(),
                        "directory": directory,
                        "total_files": 0
                    },
                    "files": {}
                }
            
            # 获取目录下所有PDF文件
            pdf_files = sorted([
                f for f in os.listdir(directory)
                if f.lower().endswith('.pdf') and not f.startswith('._')
            ])
            
            # 更新索引
            files_dict = existing_index["files"]
            current_max_index = max([int(info["index"]) for info in files_dict.values()] + [0])
            
            # 为新文件添加索引
            for file in pdf_files:
                if file not in files_dict:
                    current_max_index += 1
                    files_dict[file] = {
                        "index": current_max_index,
                        "added_at": datetime.now().isoformat(),
                        "last_analyzed": None,
                        "analysis_count": 0,
                        "included_in_summaries": []
                    }
            
            # 更新元数据
            existing_index["metadata"].update({
                "last_updated": datetime.now().isoformat(),
                "total_files": len(files_dict)
            })
            
            # 保存索引文件
            with open(index_file_path, 'w', encoding='utf-8') as f:
                json.dump(existing_index, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"文件索引已更新: {index_file_path}")
            return existing_index
            
        except Exception as e:
            self.logger.error(f"生成文件索引时发生错误: {str(e)}")
            raise
    
    def update_analysis_status(self, directory: str, filename: str) -> None:
        """更新文件的分析状态
        
        Args:
            directory: 目录路径
            filename: 文件名
        """
        try:
            index_file_path = os.path.join(directory, self.index_file_name)
            if not os.path.exists(index_file_path):
                raise FileNotFoundError(f"索引文件不存在: {index_file_path}")
            
            with open(index_file_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            if filename in index_data["files"]:
                index_data["files"][filename].update({
                    "last_analyzed": datetime.now().isoformat(),
                    "analysis_count": index_data["files"][filename]["analysis_count"] + 1
                })
                
                with open(index_file_path, 'w', encoding='utf-8') as f:
                    json.dump(index_data, f, ensure_ascii=False, indent=2)
                    
            self.logger.info(f"已更新文件分析状态: {filename}")
            
        except Exception as e:
            self.logger.error(f"更新文件分析状态时发生错误: {str(e)}")
            raise
    
    def update_summary_status(self, directory: str, filenames: List[str], summary_id: str) -> None:
        """更新文件的汇总状态
        
        Args:
            directory: 目录路径
            filenames: 文件名列表
            summary_id: 汇总ID
        """
        try:
            index_file_path = os.path.join(directory, self.index_file_name)
            if not os.path.exists(index_file_path):
                raise FileNotFoundError(f"索引文件不存在: {index_file_path}")
            
            with open(index_file_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
            
            for filename in filenames:
                if filename in index_data["files"]:
                    if summary_id not in index_data["files"][filename]["included_in_summaries"]:
                        index_data["files"][filename]["included_in_summaries"].append(summary_id)
            
            with open(index_file_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
                
            self.logger.info(f"已更新文件汇总状态: {summary_id}")
            
        except Exception as e:
            self.logger.error(f"更新文件汇总状态时发生错误: {str(e)}")
            raise
