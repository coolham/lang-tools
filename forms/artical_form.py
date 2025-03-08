from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QPushButton, QLabel, QFileDialog, QProgressBar,
                            QMessageBox, QSplitter, QFrame, QScrollArea, QComboBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from utils.logger import Logger
from services.openai_service import OpenAIService
from services.grok_service import GrokService
from services.deepseek_service import DeepseekService
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

    def __init__(self, file_path: str, ai_service, instruction: str):
        super().__init__()
        self.file_path = file_path
        self.ai_service = ai_service
        self.instruction = instruction
        self.logger = Logger.create_logger('analysis_thread')

    def run(self):
        try:
            self.status_updated.emit(f"Reading file: {os.path.basename(self.file_path)}")
            self.logger.info(f"Processing file: {self.file_path}")
            
            # 读取PDF文件
            doc = fitz.open(self.file_path)
            text_content = ""
            for page in doc:
                text_content += page.get_text()
            doc.close()
            self.logger.info(f"File reading completed: {self.file_path}")

            self.status_updated.emit(f"Analyzing file: {os.path.basename(self.file_path)}")
            # 创建AI消息
            messages = [
                Message(role="system", content=self.instruction),
                Message(role="user", content=text_content)
            ]

            # 获取AI分析结果
            response = self.ai_service.send_message(messages)
            self.logger.info(f"File analysis completed: {self.file_path}")
            self.analysis_completed.emit(os.path.basename(self.file_path), response.content)

        except Exception as e:
            self.logger.error(f"Error processing file: {self.file_path}, Error: {str(e)}")
            self.error_occurred.emit(os.path.basename(self.file_path), str(e))


class SummaryThread(QThread):
    """汇总分析线程"""
    completed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    status_updated = pyqtSignal(str)  # 状态更新信号

    def __init__(self, results: List[Dict[str, str]], ai_service, instruction: str):
        super().__init__()
        self.results = results
        self.ai_service = ai_service
        self.instruction = instruction
        self.logger = Logger.create_logger('summary_thread')

    def run(self):
        try:
            self.status_updated.emit("Generating summary report...")
            self.logger.info("Starting summary report generation")
            
            # 构建汇总内容
            summary_content = "Analysis results for each file:\n\n"
            for result in self.results:
                summary_content += f"File: {result['file']}\n"
                summary_content += f"Analysis:\n{result['content']}\n\n"

            self.status_updated.emit("Generating final summary with AI...")
            # 创建AI消息
            messages = [
                Message(role="system", content=self.instruction),
                Message(role="user", content=summary_content)
            ]

            # 获取AI汇总结果
            response = self.ai_service.send_message(messages)
            self.logger.info("Summary report generation completed")
            self.completed.emit(response.content)

        except Exception as e:
            self.logger.error(f"Error generating summary report: {str(e)}")
            self.error_occurred.emit(str(e))


class ArticleForm(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = Logger.create_logger('article')
        
        # 初始化AI服务
        self.ai_services = {
            "OpenAI": OpenAIService(),
            "Grok": GrokService(),
            "Deepseek": DeepseekService()
        }
        self.current_service = "OpenAI"  # 默认使用OpenAI
        
        self.analysis_results = []  # 存储分析结果
        self.init_ui()
        self.load_models()
        self.logger.info("Article analysis window initialized")

    def init_ui(self):
        """初始化UI布局"""
        self.setWindowTitle('Article Analysis')
        
        # 创建主布局
        main_layout = QVBoxLayout()
        
        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧分析部分
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # AI服务和模型选择区域
        ai_layout = QHBoxLayout()
        
        # 服务选择
        service_layout = QVBoxLayout()
        service_label = QLabel('AI Service:')
        self.service_combo = QComboBox()
        self.service_combo.addItems(self.ai_services.keys())
        self.service_combo.currentTextChanged.connect(self.on_service_changed)
        service_layout.addWidget(service_label)
        service_layout.addWidget(self.service_combo)
        ai_layout.addLayout(service_layout)
        
        # Provider选择（如果服务支持）
        provider_layout = QVBoxLayout()
        provider_label = QLabel('Provider:')
        self.provider_combo = QComboBox()
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(self.provider_combo)
        ai_layout.addLayout(provider_layout)
        
        # 模型选择
        model_layout = QVBoxLayout()
        model_label = QLabel('Model:')
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        ai_layout.addLayout(model_layout)
        
        ai_layout.addStretch()
        left_layout.addLayout(ai_layout)
        
        # 文件选择区域
        file_layout = QHBoxLayout()
        self.file_label = QLabel('No directory selected')
        select_dir_button = QPushButton('Select Directory')
        select_dir_button.clicked.connect(self.select_directory)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(select_dir_button)
        left_layout.addLayout(file_layout)

        # 分析指令输入区域
        instruction_layout = QVBoxLayout()
        instruction_label = QLabel('Analysis Instructions:')
        self.instruction_input = QTextEdit()
        self.instruction_input.setPlaceholderText('Enter AI analysis instructions...')
        self.instruction_input.setMaximumHeight(100)
        # 添加回车键事件处理
        self.instruction_input.keyPressEvent = self.handle_instruction_key_press
        instruction_layout.addWidget(instruction_label)
        instruction_layout.addWidget(self.instruction_input)
        
        # 添加开始分析按钮
        start_button = QPushButton('Start Analysis')
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
        summary_label = QLabel('Summary Instructions:')
        self.summary_instruction = QTextEdit()
        self.summary_instruction.setPlaceholderText('Enter AI summary instructions...')
        self.summary_instruction.setMaximumHeight(100)
        # 添加回车键事件处理
        self.summary_instruction.keyPressEvent = self.handle_summary_key_press
        summary_button = QPushButton('Generate Summary')
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

    def load_models(self):
        """加载可用的AI模型"""
        try:
            self.update_status("Loading model list...")
            service = self.ai_services[self.current_service]
            
            # 更新Provider选择（如果服务支持）
            self.provider_combo.clear()
            if hasattr(service, 'get_providers'):
                providers = service.get_providers()
                if providers:
                    self.provider_combo.addItems(providers)
                    self.provider_combo.setEnabled(True)
                    # 如果当前Provider不在列表中，选择第一个
                    if hasattr(service, 'current_provider'):
                        if service.current_provider in providers:
                            self.provider_combo.setCurrentText(service.current_provider)
                        else:
                            self.provider_combo.setCurrentText(providers[0])
            else:
                self.provider_combo.setEnabled(False)
            
            # 获取当前服务的可用模型
            models = service.get_models()
            
            # 更新下拉框
            self.model_combo.clear()
            self.model_combo.addItems(models)
            
            # 设置默认模型
            if models:
                self.model_combo.setCurrentText(models[0])
            
            self.update_status("Ready")
        except Exception as e:
            self.logger.error(f"Failed to load model list: {str(e)}")
            self.update_status(f"Failed to load models: {str(e)}")

    def on_service_changed(self, service_name: str):
        """处理AI服务选择变化"""
        try:
            self.current_service = service_name
            self.update_status(f"Switching to {service_name} service...")
            self.load_models()
            self.update_status("Ready")
        except Exception as e:
            self.logger.error(f"Failed to switch service: {str(e)}")
            self.update_status(f"Failed to switch service: {str(e)}")

    def on_provider_changed(self, provider_name: str):
        """处理Provider选择变化"""
        try:
            service = self.ai_services[self.current_service]
            if hasattr(service, 'set_provider'):
                service.set_provider(provider_name)
                self.update_status(f"Switching to provider: {provider_name}")
                # 重新加载模型列表
                models = service.get_models()
                self.model_combo.clear()
                self.model_combo.addItems(models)
                if models:
                    self.model_combo.setCurrentText(models[0])
            self.update_status("Ready")
        except Exception as e:
            self.logger.error(f"Failed to switch provider: {str(e)}")
            self.update_status(f"Failed to switch provider: {str(e)}")

    def on_model_changed(self, model_name: str):
        """处理模型选择变化"""
        try:
            self.update_status(f"Switching to model: {model_name}")
            # 更新当前服务使用的模型
            self.ai_services[self.current_service].model = model_name
            self.update_status("Ready")
        except Exception as e:
            self.logger.error(f"Failed to switch model: {str(e)}")
            self.update_status(f"Failed to switch model: {str(e)}")

    def update_status(self, message: str):
        """更新状态信息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.setWindowTitle(f'Article Analysis - [{timestamp}] {message}')
        self.logger.info(f"Status update: {message}")

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
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.file_label.setText(dir_path)
            self.logger.info(f"Selected directory: {dir_path}")
            self.update_status(f"Directory selected: {dir_path}")

    def start_analysis(self):
        """开始分析"""
        dir_path = self.file_label.text()
        if dir_path == 'No directory selected':
            self.logger.warning("No directory selected")
            QMessageBox.warning(self, "Warning", "Please select a directory first")
            return

        instruction = self.instruction_input.toPlainText().strip()
        if not instruction:
            self.logger.warning("No analysis instructions provided")
            QMessageBox.warning(self, "Warning", "Please enter analysis instructions")
            return

        # 获取目录下的所有PDF文件
        pdf_files = [f for f in os.listdir(dir_path) if f.lower().endswith('.pdf')]
        if not pdf_files:
            self.logger.warning(f"No PDF files found in directory: {dir_path}")
            QMessageBox.warning(self, "Warning", "No PDF files found in directory")
            return

        self.logger.info(f"Starting batch analysis of {len(pdf_files)} PDF files")
        self.update_status(f"Starting analysis of {len(pdf_files)} PDF files...")

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
            thread = AnalysisThread(file_path, self.ai_services[self.current_service], instruction)
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
        self.update_status(f"Analysis progress: {current}/{self.progress_bar.maximum()}")

    def handle_analysis_result(self, file_name: str, result: str):
        """处理分析结果"""
        # 保存结果
        self.analysis_results.append({
            'file': file_name,
            'content': result
        })
        self.logger.info(f"File analysis completed: {file_name}")

        # 显示结果
        result_window = AnalysisResultWindow(file_name)
        result_window.result_display.setText(result)
        self.result_layout.addWidget(result_window)

        # 检查是否所有文件都分析完成
        if len(self.analysis_results) == self.progress_bar.maximum():
            self.progress_bar.setVisible(False)
            self.update_status("All files analyzed")
            self.logger.info("All files analysis completed")
            QMessageBox.information(self, "Complete", "All files have been analyzed")

    def handle_analysis_error(self, file_name: str, error: str):
        """处理分析错误"""
        self.logger.error(f"Error analyzing file {file_name}: {error}")
        self.update_status(f"Error analyzing file {file_name}")
        QMessageBox.warning(self, "Error", f"Error analyzing file {file_name}: {error}")

    def generate_summary(self):
        """生成汇总"""
        if not self.analysis_results:
            self.logger.warning("No analysis results to summarize")
            QMessageBox.warning(self, "Warning", "No analysis results to summarize")
            return

        instruction = self.summary_instruction.toPlainText().strip()
        if not instruction:
            self.logger.warning("No summary instructions provided")
            QMessageBox.warning(self, "Warning", "Please enter summary instructions")
            return

        self.logger.info("Starting summary report generation")
        self.update_status("Generating summary report...")

        # 创建并启动汇总线程
        self.summary_thread = SummaryThread(self.analysis_results, self.ai_services[self.current_service], instruction)
        self.summary_thread.completed.connect(self.handle_summary_result)
        self.summary_thread.error_occurred.connect(self.handle_summary_error)
        self.summary_thread.status_updated.connect(self.update_status)
        self.summary_thread.start()

    def handle_summary_result(self, result: str):
        """处理汇总结果"""
        self.summary_display.setText(result)
        self.logger.info("Summary report generation completed")
        self.update_status("Summary report generated")

    def handle_summary_error(self, error: str):
        """处理汇总错误"""
        self.logger.error(f"Error generating summary report: {error}")
        self.update_status("Error generating summary report")
        QMessageBox.warning(self, "Error", f"Error generating summary report: {error}")
        
        