from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QPushButton, QLabel, QFileDialog, QProgressBar,
                            QMessageBox, QSplitter, QFrame, QScrollArea)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from utils.logger import Logger
from services.openai_service import OpenAIService
from services.models import Message
import os
import fitz  # PyMuPDF
from typing import List, Dict
from datetime import datetime


class AnalysisResultWindow(QFrame):
    """分析结果窗口"""
    def __init__(self, file_name: str, parent=None):
        super().__init__(parent)
        self.file_name = file_name
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 文件名标签
        name_label = QLabel(self.file_name)
        name_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(name_label)
        
        # 分析结果显示区域
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        layout.addWidget(self.result_display)
        
        self.setLayout(layout)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)


class AnalysisThread(QThread):
    """分析线程"""
    progress_updated = pyqtSignal(int)
    analysis_completed = pyqtSignal(str, str)  # 文件名, 分析结果
    error_occurred = pyqtSignal(str, str)  # 文件名, 错误信息
    status_updated = pyqtSignal(str)  # 状态更新信号

    def __init__(self, file_path: str, ai_service: OpenAIService, instruction: str):
        super().__init__()
        self.file_path = file_path
        self.ai_service = ai_service
        self.instruction = instruction
        self.logger = Logger.create_logger('analysis_thread')

    def run(self):
        try:
            self.status_updated.emit(f"正在读取文件: {os.path.basename(self.file_path)}")
            self.logger.info(f"开始处理文件: {self.file_path}")
            
            # 读取PDF文件
            doc = fitz.open(self.file_path)
            text_content = ""
            for page in doc:
                text_content += page.get_text()
            doc.close()
            self.logger.info(f"文件读取完成: {self.file_path}")

            self.status_updated.emit(f"正在分析文件: {os.path.basename(self.file_path)}")
            # 创建AI消息
            messages = [
                Message(role="system", content=self.instruction),
                Message(role="user", content=text_content)
            ]

            # 获取AI分析结果
            response = self.ai_service.send_message(messages)
            self.logger.info(f"文件分析完成: {self.file_path}")
            self.analysis_completed.emit(os.path.basename(self.file_path), response.content)

        except Exception as e:
            self.logger.error(f"处理文件时出错: {self.file_path}, 错误: {str(e)}")
            self.error_occurred.emit(os.path.basename(self.file_path), str(e))


class SummaryThread(QThread):
    """汇总分析线程"""
    completed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)  # 状态更新信号

    def __init__(self, results: List[Dict[str, str]], ai_service: OpenAIService, instruction: str):
        super().__init__()
        self.results = results
        self.ai_service = ai_service
        self.instruction = instruction
        self.logger = Logger.create_logger('summary_thread')

    def run(self):
        try:
            self.status_updated.emit("正在生成汇总报告...")
            self.logger.info("开始生成汇总报告")
            
            # 构建汇总内容
            summary_content = "以下是各个文件的分析结果：\n\n"
            for result in self.results:
                summary_content += f"文件：{result['file']}\n"
                summary_content += f"分析结果：\n{result['content']}\n\n"

            self.status_updated.emit("正在使用AI生成最终汇总...")
            # 创建AI消息
            messages = [
                Message(role="system", content=self.instruction),
                Message(role="user", content=summary_content)
            ]

            # 获取AI汇总结果
            response = self.ai_service.send_message(messages)
            self.logger.info("汇总报告生成完成")
            self.completed.emit(response.content)

        except Exception as e:
            self.logger.error(f"生成汇总报告时出错: {str(e)}")
            self.error_occurred.emit(str(e))


class ArticleForm(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = Logger.create_logger('article')
        self.ai_service = OpenAIService()
        self.analysis_results = []  # 存储分析结果
        self.init_ui()
        self.logger.info("论文分析窗口初始化完成")

    def init_ui(self):
        """初始化UI布局"""
        self.setWindowTitle('论文分析')
        
        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧分析部分
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        self.file_label = QLabel('未选择目录')
        select_dir_button = QPushButton('选择目录')
        select_dir_button.clicked.connect(self.select_directory)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(select_dir_button)
        left_layout.addLayout(file_layout)

        # 分析指令输入区域
        instruction_layout = QVBoxLayout()
        instruction_label = QLabel('分析指令：')
        self.instruction_input = QTextEdit()
        self.instruction_input.setPlaceholderText('请输入AI分析指令...')
        self.instruction_input.setMaximumHeight(100)
        # 添加回车键事件处理
        self.instruction_input.keyPressEvent = self.handle_instruction_key_press
        instruction_layout.addWidget(instruction_label)
        instruction_layout.addWidget(self.instruction_input)
        
        # 添加开始分析按钮
        start_button = QPushButton('开始分析')
        start_button.clicked.connect(self.start_analysis)
        instruction_layout.addWidget(start_button)
        
        left_layout.addLayout(instruction_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        left_layout.addWidget(self.progress_bar)

        # 分析结果显示区域
        self.result_scroll = QScrollArea()
        self.result_scroll.setWidgetResizable(True)
        self.result_container = QWidget()
        self.result_layout = QVBoxLayout(self.result_container)
        self.result_scroll.setWidget(self.result_container)
        left_layout.addWidget(self.result_scroll)

        # 右侧汇总部分
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # 汇总区域
        summary_layout = QVBoxLayout()
        summary_label = QLabel('汇总指令：')
        self.summary_instruction = QTextEdit()
        self.summary_instruction.setPlaceholderText('请输入AI汇总指令...')
        self.summary_instruction.setMaximumHeight(100)
        # 添加回车键事件处理
        self.summary_instruction.keyPressEvent = self.handle_summary_key_press
        summary_button = QPushButton('生成汇总')
        summary_button.clicked.connect(self.generate_summary)
        summary_layout.addWidget(summary_label)
        summary_layout.addWidget(self.summary_instruction)
        summary_layout.addWidget(summary_button)
        right_layout.addLayout(summary_layout)

        # 汇总结果显示区域
        self.summary_display = QTextEdit()
        self.summary_display.setReadOnly(True)
        right_layout.addWidget(self.summary_display)

        # 添加左右部件到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        
        # 设置分割器的初始大小
        splitter.setSizes([self.width() // 2, self.width() // 2])
        
        # 将分割器添加到主布局
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)

    def update_status(self, message: str):
        """更新状态信息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.setWindowTitle(f'论文分析 - [{timestamp}] {message}')
        self.logger.info(f"状态更新: {message}")

    def handle_instruction_key_press(self, event):
        """处理分析指令输入框的按键事件"""
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.start_analysis()
        else:
            QTextEdit.keyPressEvent(self.instruction_input, event)

    def handle_summary_key_press(self, event):
        """处理汇总指令输入框的按键事件"""
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.generate_summary()
        else:
            QTextEdit.keyPressEvent(self.summary_instruction, event)

    def select_directory(self):
        """选择目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if dir_path:
            self.file_label.setText(dir_path)
            self.logger.info(f"选择目录: {dir_path}")
            self.update_status(f"已选择目录: {dir_path}")

    def start_analysis(self):
        """开始分析"""
        dir_path = self.file_label.text()
        if dir_path == '未选择目录':
            self.logger.warning("未选择目录")
            QMessageBox.warning(self, "警告", "请先选择目录")
            return

        instruction = self.instruction_input.toPlainText().strip()
        if not instruction:
            self.logger.warning("未输入分析指令")
            QMessageBox.warning(self, "警告", "请输入分析指令")
            return

        # 获取目录下的所有PDF文件
        pdf_files = [f for f in os.listdir(dir_path) if f.lower().endswith('.pdf')]
        if not pdf_files:
            self.logger.warning(f"目录中没有PDF文件: {dir_path}")
            QMessageBox.warning(self, "警告", "目录中没有PDF文件")
            return

        self.logger.info(f"开始批量分析PDF文件，共{len(pdf_files)}个文件")
        self.update_status(f"开始分析{len(pdf_files)}个PDF文件...")

        # 清空之前的结果
        self.analysis_results.clear()
        while self.result_layout.count():
            item = self.result_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 设置进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(pdf_files))
        self.progress_bar.setValue(0)

        # 创建并启动分析线程
        self.analysis_threads = []
        for pdf_file in pdf_files:
            file_path = os.path.join(dir_path, pdf_file)
            thread = AnalysisThread(file_path, self.ai_service, instruction)
            thread.progress_updated.connect(self.update_progress)
            thread.analysis_completed.connect(self.handle_analysis_result)
            thread.error_occurred.connect(self.handle_analysis_error)
            thread.status_updated.connect(self.update_status)
            thread.start()
            self.analysis_threads.append(thread)

    def update_progress(self):
        """更新进度条"""
        current = self.progress_bar.value() + 1
        self.progress_bar.setValue(current)
        self.update_status(f"分析进度: {current}/{self.progress_bar.maximum()}")

    def handle_analysis_result(self, file_name: str, result: str):
        """处理分析结果"""
        # 保存结果
        self.analysis_results.append({
            'file': file_name,
            'content': result
        })
        self.logger.info(f"文件分析完成: {file_name}")

        # 显示结果
        result_window = AnalysisResultWindow(file_name)
        result_window.result_display.setText(result)
        self.result_layout.addWidget(result_window)

        # 检查是否所有文件都分析完成
        if len(self.analysis_results) == self.progress_bar.maximum():
            self.progress_bar.setVisible(False)
            self.update_status("所有文件分析完成")
            self.logger.info("所有文件分析完成")
            QMessageBox.information(self, "完成", "所有文件分析完成")

    def handle_analysis_error(self, file_name: str, error: str):
        """处理分析错误"""
        self.logger.error(f"分析文件 {file_name} 时出错: {error}")
        self.update_status(f"分析文件 {file_name} 时出错")
        QMessageBox.warning(self, "错误", f"分析文件 {file_name} 时出错: {error}")

    def generate_summary(self):
        """生成汇总"""
        if not self.analysis_results:
            self.logger.warning("没有可汇总的分析结果")
            QMessageBox.warning(self, "警告", "没有可汇总的分析结果")
            return

        instruction = self.summary_instruction.toPlainText().strip()
        if not instruction:
            self.logger.warning("未输入汇总指令")
            QMessageBox.warning(self, "警告", "请输入汇总指令")
            return

        self.logger.info("开始生成汇总报告")
        self.update_status("正在生成汇总报告...")

        # 创建并启动汇总线程
        self.summary_thread = SummaryThread(self.analysis_results, self.ai_service, instruction)
        self.summary_thread.completed.connect(self.handle_summary_result)
        self.summary_thread.error_occurred.connect(self.handle_summary_error)
        self.summary_thread.status_updated.connect(self.update_status)
        self.summary_thread.start()

    def handle_summary_result(self, result: str):
        """处理汇总结果"""
        self.summary_display.setText(result)
        self.logger.info("汇总报告生成完成")
        self.update_status("汇总报告生成完成")

    def handle_summary_error(self, error: str):
        """处理汇总错误"""
        self.logger.error(f"生成汇总报告时出错: {error}")
        self.update_status("生成汇总报告时出错")
        QMessageBox.warning(self, "错误", f"生成汇总报告时出错: {error}")
        
        