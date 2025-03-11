from PyQt6.QtCore import QThread, pyqtSignal
from utils.logger import Logger
from services.message_types import Message
from typing import List, Dict
import os
from PyQt6.QtWidgets import QMessageBox
from datetime import datetime

class SummaryThread(QThread):
    """汇总分析线程"""
    completed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)  # 状态更新信号
    
    def __init__(self, results: List[Dict[str, str]], ai_service, instruction: str):
        """初始化汇总线程"""
        super().__init__()
        self.results = results
        self.ai_service = ai_service
        self.instruction = instruction
        self.logger = Logger.create_logger('summary_thread')
        self.is_running = False
        self.logger.info("汇总线程已初始化")
        self.logger.info(f"待汇总文件数量: {len(results)}")

    def __del__(self):
        """析构函数"""
        try:
            self.logger.info("汇总线程开始销毁")
            if self.is_running:
                self.logger.info("等待线程完成...")
                self.wait()
            self.logger.info("汇总线程销毁完成")
        except Exception as e:
            # 避免在析构时抛出异常
            pass

    def run(self):
        """运行汇总线程"""

        try:
            self.is_running = True
            self.logger.info("开始生成汇总报告")
            self.logger.info(f"收到的原始数据: {self.results}")
            
            # 构建汇总内容
            summary_content = []
            for item in self.results:
                try:
                    self.logger.info(f"正在处理文件: {item.get('filename', '')}")
                    self.logger.info(f"当前item的完整内容: {item}")
                    
                    # 检查是否是分析结果字典
                    if isinstance(item, tuple) and len(item) == 2:
                        # 如果是元组，说明是(file_path, content)格式
                        file_path, content = item
                        item = {
                            "file_path": file_path,
                            "filename": os.path.basename(file_path),
                            "directory": os.path.dirname(file_path),
                            "content": content,
                            "analysis_status": "已分析"
                        }
                    
                    # 验证必要字段
                    required_fields = ['filename', 'analysis_result']  # 修改必要字段
                    missing_fields = [field for field in required_fields if not item.get(field)]
                    if missing_fields:
                        self.logger.warning(f"文件缺少必要字段: {missing_fields}")
                        self.logger.warning(f"当前item的内容: {item}")
                        continue
                    
                    # 获取文件信息，保持与AnalysisThread输出的一致性
                    file_info = {
                        "global_index": item.get("global_index", "N/A"),
                        "filename": item.get("filename", ""),
                        "directory": item.get("directory", ""),
                        "file_path": item.get("file_path", ""),
                        "analysis_status": "已分析",
                        "analysis_time": item.get("analysis_time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    }
                    
                    # 获取分析结果
                    analysis_content = item.get("analysis_result", "")  # 修改为使用analysis_result
                    if not analysis_content:
                        # 尝试从其他可能的字段获取内容
                        analysis_content = item.get("content", "")  # 尝试从content字段获取
                        if not analysis_content:
                            self.logger.warning(f"文件 {file_info['filename']} 的分析结果为空")
                            continue
                    
                    # 构建单个文件的汇总内容
                    file_content = {
                        "file_info": file_info,
                        "analysis": analysis_content
                    }
                    summary_content.append(file_content)
                    self.logger.info(f"成功添加文件 {file_info['filename']} 的汇总内容")
                    
                except Exception as e:
                    self.logger.error(f"处理文件信息时出现错误: {str(e)}")
                    self.logger.error(f"当前item内容: {item}")
                    continue
            
            if not summary_content:
                self.logger.error("没有有效的汇总内容可用")
                raise ValueError("没有有效的汇总内容")
            
            self.logger.info(f"成功处理的文件数量: {len(summary_content)}")
            
            # 按global_index排序
            summary_content.sort(key=lambda x: str(x["file_info"]["global_index"]))
            
            # 构建增强的指令
            enhanced_instruction = f"""
{self.instruction}

请严格按照以下格式生成汇总报告：

1. 汇总表格：
| 序号 | 论文标题 | 实现类型 | 判断依据 | 代码开源 |
|------|---------|----------|----------|----------|

注意事项：
1. 序号：使用文件的global_index（已排序）
2. 论文标题：使用完整标题
3. 实现类型：必须是"official"、"unofficial"或"未知"
4. 判断依据：简要说明判断实现类型的具体证据
5. 代码开源：必须是"是"或"否"

2. 统计信息：
- 分析论文总数
- 官方实现（official）数量和占比
- 非官方实现（unofficial）数量和占比
- 未知类型数量和占比
- 代码开源数量和占比

待分析的文件信息如下：
"""
            
            # 将文件信息格式化为易于AI处理的形式
            formatted_content = []
            for item in summary_content:
                file_info = item["file_info"]
                analysis = item["analysis"]
                
                # 提取文件名（去除.pdf后缀）
                title = file_info['filename'].replace('.pdf', '')
                
                formatted_item = (
                    f"文件 {file_info['global_index']}：\n"
                    f"- 标题: {title}\n"
                    f"- 分析时间: {file_info['analysis_time']}\n"
                    f"- 分析结果:\n{analysis}\n"
                    f"---\n"
                )
                formatted_content.append(formatted_item)
            
            # 准备AI消息
            messages = [
                Message(role="system", content="你是一个专业的论文分析助手。请严格按照指定格式生成汇总报告，确保包含所有必要的统计信息。对于每篇论文的实现类型判断必须基于分析结果中的具体证据。"),
                Message(role="user", content=f"{enhanced_instruction}\n\n{'\n'.join(formatted_content)}")
            ]
            
            # 发送到AI服务
            self.logger.info("正在发送到AI服务进行汇总...")
            response = self.ai_service.send_message(messages)
            
            if response and hasattr(response, 'choices') and response.choices:
                result = response.choices[0].message.content
                
                # 添加汇总报告头部信息
                header = (
                    "# 论文分析汇总报告\n\n"
                    f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"- 分析文件数：{len(summary_content)}\n"
                    "- 说明：使用全局唯一的文件编号(global_index)作为序号\n\n"
                    "---\n\n"
                )
                
                final_result = header + result
                self.logger.info(f"收到AI响应，长度: {len(final_result)}")
                self.completed.emit(final_result)
            else:
                raise ValueError("未收到有效的AI响应")
                
        except Exception as e:
            self.logger.error(f"汇总报告生成失败: {str(e)}")
            self.error_occurred.emit(str(e))
        finally:
            self.is_running = False
            self.logger.info("汇总线程执行完成")

def generate_summary(self):
    """生成汇总报告"""
    try:
        if not self.analysis_results:
            self.logger.warning("没有可用的分析结果")
            QMessageBox.warning(self, "警告", "请先完成文件分析")
            return
        
        # 获取汇总指令
        instruction = self.summary_instruction.toPlainText().strip()
        if not instruction:
            instruction = self.prompt_manager.get_prompt('summary')
            if not instruction:
                QMessageBox.warning(self, "警告", "汇总指令不能为空")
                return
        
        # 禁用所有按钮
        self.summary_button.setEnabled(False)
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.save_button.setEnabled(False)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(0)  # 设置为循环进度条
        
        # 准备汇总数据，添加完整的文件信息
        summary_data = []
        for file_path, content in sorted(self.analysis_results.items()):
            file_info = {
                "file_path": file_path,                      # 完整路径
                "directory": os.path.dirname(file_path),     # 目录
                "filename": os.path.basename(file_path),     # 文件名
                "content": content                           # 分析内容
            }
            summary_data.append(file_info)
        
        # 记录文件数量
        self.logger.info(f"准备汇总的文件数量: {len(summary_data)}")
        
        # 修改汇总指令，添加文件信息要求
        enhanced_instruction = (
            "请在生成汇总表格时，确保包含以下信息：\n"
            "1. 添加一列显示文件所在目录\n"
            "2. 添加一列显示文件名\n"
            "3. 请严格按照输入的文件顺序进行汇总\n"
            "4. 确保汇总的文件数量与输入的文件数量一致\n\n"
            "原始汇总指令：\n"
            f"{instruction}"
        )
        
        # 创建新的汇总线程
        self.summary_thread = SummaryThread(
            summary_data,
            self.ai_services[self.current_service],
            enhanced_instruction
        )
        
        # 连接信号
        self.summary_thread.completed.connect(self.handle_summary_result)
        self.summary_thread.error_occurred.connect(self.handle_summary_error)
        self.summary_thread.status_updated.connect(self.update_status)
        
        # 启动线程
        self.summary_thread.start()
        self.update_status("正在生成汇总报告...")
        
    except Exception as e:
        self.logger.error(f"生成汇总报告时发生错误: {str(e)}")
        QMessageBox.critical(self, "错误", f"生成汇总报告时发生错误: {str(e)}")
        self.reset_ui_state()

def handle_summary_result(self, result: str):
    """处理汇总结果"""
    try:
        self.logger.info("收到汇总结果")
        
        # 验证汇总结果的完整性
        original_count = len(self.analysis_results)
        # 简单的行数检查（这是一个基本检查，可能需要更复杂的解析）
        result_lines = result.split('\n')
        table_lines = [line for line in result_lines if '|' in line]
        # 减去表头和分隔行
        table_content_lines = len(table_lines) - 2
        
        if table_content_lines != original_count:
            warning_msg = (
                f"警告：汇总结果的记录数 ({table_content_lines}) "
                f"与原始分析文件数 ({original_count}) 不一致！\n"
                "是否要重新生成汇总报告？"
            )
            reply = QMessageBox.warning(
                self,
                "数量不一致",
                warning_msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self.generate_summary()
                return
        
        # 隐藏进度条
        self.progress_bar.setVisible(False)
        
        # 在汇总结果开头添加统计信息
        header = (
            f"# 论文分析汇总报告\n\n"
            f"- 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"- 分析文件数：{original_count}\n"
            f"- 汇总记录数：{table_content_lines}\n\n"
            "---\n\n"
        )
        
        # 显示汇总结果
        self.summary_display.setText(header + result)
        self.logger.info("汇总结果已显示")
        
        # 恢复按钮状态
        self.summary_button.setEnabled(True)
        self.start_button.setEnabled(True)
        self.save_button.setEnabled(True)
        
        # 更新状态
        self.update_status("汇总报告已生成")
        
        # 显示完成对话框
        QMessageBox.information(
            self,
            "汇总完成",
            f"汇总报告已生成完成\n\n"
            f"- 原始分析文件数：{original_count}\n"
            f"- 汇总记录数：{table_content_lines}"
        )
        
    except Exception as e:
        self.logger.error(f"处理汇总结果时发生错误: {str(e)}")
        QMessageBox.critical(self, "错误", f"处理汇总结果时发生错误: {str(e)}")
        self.reset_ui_state()
    finally:
        # 清理线程
        if hasattr(self, 'summary_thread') and self.summary_thread is not None:
            self.summary_thread.deleteLater()
            self.summary_thread = None