import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QLabel, QFileDialog, QProgressBar,
                             QMessageBox, QSplitter, QFrame, QScrollArea, QComboBox,
                             QDialog, QListWidget, QListWidgetItem, QGroupBox, QGraphicsEffect)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont
from utils.logger import Logger
from services.openai_service import OpenAIService
from services.grok_service import GrokService
from services.deepseek_service import DeepseekService
from utils.prompt_manager import PromptManager
from utils.config_manager import ConfigManager
from datetime import datetime
from forms.analysis_result_window import AnalysisResultWindow
from threads.analysis_thread import AnalysisThread
from threads.summary_thread import SummaryThread
from utils.file_index_manager import FileIndexManager
from widgets.file_selection_dialog import FileSelectionDialog

"""
分析论文的UI
"""


class ArticleAnalysisForm(QWidget):
    def __init__(self):
        try:
            super().__init__()
            self.logger = Logger.create_logger('article')
            self.logger.info("开始初始化ArticleForm...")

            # 初始化提示词管理器
            self.prompt_manager = PromptManager()

            # 初始化文件索引管理器
            self.file_index_manager = FileIndexManager(self.logger)
            self.current_directory = None
            self.file_index = None

            # 添加停止分析的标志
            self.is_analyzing = False
            self.analysis_threads = []
            self.selected_files = []  # 存储选中的文件列表

            # 存储分析结果
            self.analysis_results = {}  # 用于存储分析结果

            # 添加提示词更改标志
            self.has_unsaved_analysis_changes = False
            self.has_unsaved_summary_changes = False

            try:
                # 初始化配置管理器
                self.logger.info("初始化配置管理器...")
                config_manager = ConfigManager()

                # 初始化AI服务
                self.logger.info("开始初始化AI服务...")
                self.ai_services = {}

                # 逐个初始化服务，并记录日志
                try:
                    self.logger.info("初始化OpenAI服务...")
                    self.ai_services["OpenAI"] = OpenAIService(config_manager=config_manager)
                except Exception as e:
                    self.logger.error(f"初始化OpenAI服务失败: {str(e)}")

                try:
                    self.logger.info("初始化Grok服务...")
                    self.ai_services["Grok"] = GrokService(config_manager=config_manager)
                except Exception as e:
                    self.logger.error(f"初始化Grok服务失败: {str(e)}")

                try:
                    self.logger.info("初始化Deepseek服务...")
                    self.ai_services["Deepseek"] = DeepseekService(config_manager=config_manager)
                except Exception as e:
                    self.logger.error(f"初始化Deepseek服务失败: {str(e)}")

                if not self.ai_services:
                    raise RuntimeError("没有可用的AI服务")

                # self.current_service = next(iter(self.ai_services.keys()))  # 使用第一个可用的服务
                self.current_service = "Grok"

                self.logger.info(f"默认使用服务: {self.current_service}")

                self.logger.info("开始初始化UI...")
                self.init_ui()
                self.logger.info("UI初始化完成")

                self.logger.info("开始加载模型...")
                try:
                    self.load_models()
                    self.logger.info("模型加载完成")
                except Exception as e:
                    self.logger.error(f"加载模型失败: {str(e)}")
                    raise

                self.logger.info("ArticleForm初始化完成")

            except Exception as e:
                self.logger.error(f"ArticleForm初始化失败: {str(e)}")
                raise  # 重新抛出异常，让上层处理

        except Exception as e:
            self.logger.error(f"ArticleForm创建失败: {str(e)}")
            # 显示错误对话框
            QMessageBox.critical(None, "错误", f"程序初始化失败: {str(e)}")
            raise

    def init_ui(self):
        """初始化UI布局"""
        self.setWindowTitle('Article Analysis')

        # 创建主布局
        main_layout = QVBoxLayout()

        # 创建上下分割器
        main_splitter = QSplitter(Qt.Orientation.Vertical)

        # 上半部分：控制面板
        top_widget = QWidget()
        top_layout = QVBoxLayout()

        # 初始化各个功能区域
        control_panel = QHBoxLayout()
        control_panel.addWidget(self._init_instruction_config())  # 指令配置
        control_panel.addWidget(self._init_service_config())  # AI服务配置
        top_layout.addLayout(control_panel)

        # 文件选择区域
        # top_layout.addWidget(self._init_file_selection())

        top_widget.setLayout(top_layout)
        main_splitter.addWidget(top_widget)

        # 下半部分：结果显示区域
        bottom_splitter = QSplitter(Qt.Orientation.Horizontal)
        bottom_splitter.addWidget(self._init_analysis_display())  # 分析结果显示
        bottom_splitter.addWidget(self._init_summary_display())  # 汇总结果显示

        # 设置分割比例
        bottom_splitter.setStretchFactor(0, 1)  # 分析结果区域
        bottom_splitter.setStretchFactor(1, 1)  # 汇总结果区域

        main_splitter.addWidget(bottom_splitter)

        # 设置主分割器比例
        main_splitter.setStretchFactor(0, 1)  # 上半部分
        main_splitter.setStretchFactor(1, 2)  # 下半部分

        main_layout.addWidget(main_splitter)

        # 底部控制区域
        main_layout.addLayout(self._init_bottom_controls())

        self.setLayout(main_layout)
        self.logger.info("UI初始化完成")

    def _init_service_config(self) -> QGroupBox:
        """初始化AI服务配置面板"""
        service_group = QGroupBox("AI服务配置")
        service_layout = QVBoxLayout()

        # 服务选择
        service_combo = QComboBox()
        service_combo.addItems(self.ai_services.keys())
        service_combo.setCurrentText(self.current_service)
        service_combo.currentTextChanged.connect(self.on_service_changed)
        service_layout.addWidget(QLabel("选择服务:"))
        service_layout.addWidget(service_combo)

        # 提供商选择
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(self.ai_services[self.current_service].get_providers())
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        service_layout.addWidget(QLabel("选择提供商:"))
        service_layout.addWidget(self.provider_combo)

        # 模型选择
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        service_layout.addWidget(QLabel("选择模型:"))
        service_layout.addWidget(self.model_combo)

        # 文件选择
        service_layout.addWidget(self._init_file_selection())

        service_group.setLayout(service_layout)
        return service_group

    def _init_instruction_config(self) -> QGroupBox:
        """初始化指令配置面板"""
        instruction_group = QGroupBox("分析指令配置")
        instruction_layout = QHBoxLayout()

        # 单篇分析指令
        analysis_group = QGroupBox("单篇分析指令")
        analysis_layout = QVBoxLayout()

        # 添加状态标签
        self.analysis_status_label = QLabel()
        self.analysis_status_label.setStyleSheet("""
            QLabel {
                padding: 2px 5px;
                font-size: 10pt;
            }
        """)
        analysis_layout.addWidget(self.analysis_status_label)

        # 按钮布局
        analysis_header_layout = QHBoxLayout()

        # 添加保存和重置按钮
        save_analysis_btn = QPushButton("保存")
        save_analysis_btn.setToolTip("保存当前的分析指令作为自定义指令")
        save_analysis_btn.clicked.connect(lambda: self.save_prompt('analysis'))

        reset_analysis_btn = QPushButton("重置")
        reset_analysis_btn.setToolTip("重置为默认的分析指令")
        reset_analysis_btn.clicked.connect(lambda: self.reset_prompt('analysis'))

        analysis_header_layout.addWidget(save_analysis_btn)
        analysis_header_layout.addWidget(reset_analysis_btn)
        analysis_layout.addLayout(analysis_header_layout)

        # 分析指令文本框
        self.analysis_instruction = self._create_instruction_text_edit('analysis')
        self.analysis_instruction.textChanged.connect(lambda: self._update_prompt_status('analysis'))
        analysis_layout.addWidget(self.analysis_instruction)

        analysis_group.setLayout(analysis_layout)
        instruction_layout.addWidget(analysis_group)

        # 汇总分析指令
        summary_group = QGroupBox("汇总分析指令")
        summary_layout = QVBoxLayout()

        # 添加状态标签
        self.summary_status_label = QLabel()
        self.summary_status_label.setStyleSheet("""
            QLabel {
                padding: 2px 5px;
                font-size: 10pt;
            }
        """)
        summary_layout.addWidget(self.summary_status_label)

        # 按钮布局
        summary_header_layout = QHBoxLayout()

        # 添加保存和重置按钮
        save_summary_btn = QPushButton("保存")
        save_summary_btn.setToolTip("保存当前的汇总指令作为自定义指令")
        save_summary_btn.clicked.connect(lambda: self.save_prompt('summary'))

        reset_summary_btn = QPushButton("重置")
        reset_summary_btn.setToolTip("重置为默认的汇总指令")
        reset_summary_btn.clicked.connect(lambda: self.reset_prompt('summary'))

        summary_header_layout.addWidget(save_summary_btn)
        summary_header_layout.addWidget(reset_summary_btn)
        summary_layout.addLayout(summary_header_layout)

        # 汇总指令文本框
        self.summary_instruction = self._create_instruction_text_edit('summary')
        self.summary_instruction.textChanged.connect(lambda: self._update_prompt_status('summary'))
        summary_layout.addWidget(self.summary_instruction)

        summary_group.setLayout(summary_layout)
        instruction_layout.addWidget(summary_group)

        instruction_group.setLayout(instruction_layout)

        # 初始化状态显示
        self._update_prompt_status('analysis')
        self._update_prompt_status('summary')

        return instruction_group

    def _create_instruction_text_edit(self, instruction_type: str) -> QTextEdit:
        """创建指令文本编辑器
        
        Args:
            instruction_type: 指令类型 ('analysis' 或 'summary')
            
        Returns:
            QTextEdit: 配置好的文本编辑器
        """
        text_edit = QTextEdit()

        # 获取提示词（优先获取自定义提示词）
        prompt = self.prompt_manager.get_prompt(instruction_type, use_custom=True)
        if prompt:
            text_edit.setPlainText(prompt)
            self.logger.info(
                f"已加载{instruction_type}{'自定义' if prompt == self.prompt_manager.prompts[instruction_type]['custom'] else '默认'}提示词")

        # 设置占位符文本
        placeholder = ("在此输入分析指令...\n\n提示：\n1. 使用 Ctrl+Enter 快捷键开始分析\n"
                       "2. 使用等宽字体便于编辑格式化文本\n3. 可以使用 Markdown 格式\n"
                       "4. 点击保存按钮可以保存为自定义指令") if instruction_type == 'analysis' else \
            ("在此输入汇总指令...\n\n提示：\n1. 使用 Ctrl+Enter 快捷键生成汇总\n"
             "2. 支持 Markdown 表格格式\n3. 可以自定义分类方式\n"
             "4. 点击保存按钮可以保存为自定义指令")
        text_edit.setPlaceholderText(placeholder)

        # 设置文本编辑器样式
        text_edit.setMinimumHeight(300)
        text_edit.setFont(QFont("Consolas", 10))
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 8px;
                line-height: 1.5;
            }
            QTextEdit:focus {
                border: 2px solid #80bdff;
            }
        """)

        return text_edit

    def _init_file_selection(self) -> QGroupBox:
        """初始化文件选择面板"""
        file_selection_group = QGroupBox("文件选择")
        file_selection_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-top: 1em;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #495057;
            }
        """)

        file_selection_layout = QVBoxLayout()

        # 按钮区域
        button_layout = QHBoxLayout()
        select_dir_btn = QPushButton("选择目录")
        select_dir_btn.clicked.connect(self.select_directory)
        select_files_btn = QPushButton("选择文件")
        select_files_btn.clicked.connect(self.show_file_selection_dialog)

        # 文件选择按钮样式
        file_button_style = """
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #545b62;
            }
        """
        select_dir_btn.setStyleSheet(file_button_style)
        select_files_btn.setStyleSheet(file_button_style)

        button_layout.addWidget(select_dir_btn)
        button_layout.addWidget(select_files_btn)
        button_layout.addStretch()
        file_selection_layout.addLayout(button_layout)

        # 已选文件显示区域
        file_list_label = QLabel("已选择的文件:")
        file_list_label.setStyleSheet("""
            QLabel {
                color: #495057;
                font-weight: bold;
                margin-top: 10px;
            }
        """)
        file_selection_layout.addWidget(file_list_label)

        self.selected_files_display = QTextEdit()
        self.selected_files_display.setReadOnly(True)
        self.selected_files_display.setMaximumHeight(100)
        self.selected_files_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 8px;
                font-family: "Consolas", monospace;
                font-size: 10pt;
                line-height: 1.4;
            }
        """)
        file_selection_layout.addWidget(self.selected_files_display)

        file_selection_group.setLayout(file_selection_layout)
        return file_selection_group

    def _init_analysis_display(self) -> QWidget:
        """初始化分析结果显示区域"""
        analysis_widget = QWidget()
        analysis_layout = QVBoxLayout()

        # 分析结果标题和计数
        analysis_header = QHBoxLayout()
        analysis_title = QLabel("分析结果")
        analysis_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px;
            }
        """)
        analysis_header.addWidget(analysis_title)

        self.analysis_count_label = QLabel("0/0")
        self.analysis_count_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                font-weight: bold;
                padding: 5px;
                background-color: #f8f9fa;
                border-radius: 4px;
                margin-left: 10px;
            }
        """)
        analysis_header.addWidget(self.analysis_count_label)
        analysis_header.addStretch()
        analysis_layout.addLayout(analysis_header)

        # 分析结果滚动区域
        analysis_scroll = QScrollArea()
        analysis_scroll.setWidgetResizable(True)
        analysis_scroll.setMinimumHeight(400)
        analysis_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #f8f9fa;
                width: 10px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #dee2e6;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)

        analysis_content = QWidget()
        self.result_layout = QVBoxLayout()
        self.result_layout.setSpacing(10)
        self.result_layout.setContentsMargins(5, 5, 5, 5)
        analysis_content.setLayout(self.result_layout)
        analysis_scroll.setWidget(analysis_content)
        analysis_layout.addWidget(analysis_scroll)

        # 添加控制按钮
        analysis_layout.addLayout(self._create_control_buttons())

        analysis_widget.setLayout(analysis_layout)
        return analysis_widget

    def _create_control_buttons(self) -> QHBoxLayout:
        """创建控制按钮"""
        button_style = """
            QPushButton {
                background-color: %(bg_color)s;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 100px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: %(hover_color)s;
            }
            QPushButton:pressed {
                background-color: %(pressed_color)s;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                opacity: 0.65;
            }
        """

        self.start_button = QPushButton("开始分析")
        self.start_button.clicked.connect(self.start_analysis)
        self.start_button.setStyleSheet(button_style % {
            'bg_color': '#28a745',
            'hover_color': '#218838',
            'pressed_color': '#1e7e34'
        })

        self.stop_button = QPushButton("停止分析")
        self.stop_button.clicked.connect(self.stop_analysis)
        self.stop_button.setStyleSheet(button_style % {
            'bg_color': '#dc3545',
            'hover_color': '#c82333',
            'pressed_color': '#bd2130'
        })

        self.summary_button = QPushButton("生成汇总")
        self.summary_button.clicked.connect(self.generate_summary)
        self.summary_button.setStyleSheet(button_style % {
            'bg_color': '#007bff',
            'hover_color': '#0056b3',
            'pressed_color': '#004085'
        })

        self.save_button = QPushButton("保存汇总")
        self.save_button.clicked.connect(self.save_summary)
        self.save_button.setStyleSheet(button_style % {
            'bg_color': '#17a2b8',
            'hover_color': '#138496',
            'pressed_color': '#117a8b'
        })

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.summary_button)
        button_layout.addWidget(self.save_button)

        return button_layout

    def _init_summary_display(self) -> QWidget:
        """初始化汇总结果显示区域"""
        summary_widget = QWidget()
        summary_layout = QVBoxLayout()

        # 汇总结果标题
        summary_header = QHBoxLayout()
        summary_title = QLabel("汇总结果")
        summary_title.setStyleSheet("""
            QLabel {
                font-size: 14px;
                font-weight: bold;
                color: #2c3e50;
                padding: 5px;
            }
        """)
        summary_header.addWidget(summary_title)
        summary_header.addStretch()
        summary_layout.addLayout(summary_header)

        # 汇总结果显示区域
        self.summary_display = QTextEdit()
        self.summary_display.setReadOnly(True)
        self.summary_display.setFont(QFont("Consolas", 10))
        self.summary_display.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 12px;
                line-height: 1.6;
            }
            QTextEdit:focus {
                border-color: #80bdff;
                outline: 0;
                box-shadow: 0 0 0 0.2rem rgba(0,123,255,.25);
            }
        """)
        summary_layout.addWidget(self.summary_display)

        summary_widget.setLayout(summary_layout)
        return summary_widget

    def _init_bottom_controls(self) -> QHBoxLayout:
        """初始化底部控制区域"""
        bottom_layout = QHBoxLayout()

        # 进度条样式
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                text-align: center;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)

        # 状态标签样式
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            QLabel {
                color: #495057;
                padding: 5px;
                font-size: 12px;
            }
        """)

        # 左侧：状态和进度
        status_layout = QHBoxLayout()
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.progress_bar)
        bottom_layout.addLayout(status_layout)

        return bottom_layout

    def load_models(self):
        """加载可用的AI模型"""
        try:
            self.update_status("正在加载模型列表...")
            self.logger.info(f"开始加载{self.current_service}服务的模型列表...")

            if not hasattr(self, 'current_service'):
                raise ValueError("current_service未初始化")

            if not hasattr(self, 'ai_services'):
                raise ValueError("ai_services未初始化")

            if self.current_service not in self.ai_services:
                raise ValueError(f"服务{self.current_service}未初始化")

            service = self.ai_services[self.current_service]
            self.logger.info(f"获取到服务实例: {type(service).__name__}")

            # 更新Provider选择（如果服务支持）
            self.provider_combo.clear()
            if hasattr(service, 'get_providers'):
                self.logger.info("获取服务提供商列表...")
                try:
                    providers = service.get_providers()
                    self.logger.info(f"可用的服务提供商: {providers}")
                    if providers:
                        self.provider_combo.addItems(providers)
                        self.provider_combo.setEnabled(True)
                        # 如果当前Provider不在列表中，选择第一个
                        if hasattr(service, 'provider_name'):
                            if service.provider_name in providers:
                                self.provider_combo.setCurrentText(service.provider_name)
                                self.logger.info(f"设置当前提供商: {service.provider_name}")
                            else:
                                self.provider_combo.setCurrentText(providers[0])
                                self.logger.info(f"设置默认提供商: {providers[0]}")
                    else:
                        self.logger.warning("没有可用的服务提供商")
                        self.provider_combo.setEnabled(False)
                except Exception as e:
                    self.logger.error(f"获取提供商列表失败: {str(e)}")
                    self.provider_combo.setEnabled(False)
            else:
                self.logger.info("当前服务不支持多提供商")
                self.provider_combo.setEnabled(False)

            # 获取当前服务的可用模型
            self.logger.info("获取可用模型列表...")
            try:
                if not hasattr(service, 'get_models'):
                    raise AttributeError(f"服务{type(service).__name__}没有get_models方法")

                models = service.get_models()
                self.logger.info(f"可用的模型: {models}")

                if not models:
                    raise ValueError("没有可用的模型")

                # 更新下拉框
                self.model_combo.clear()
                self.model_combo.addItems(models)

                # 设置默认模型
                if hasattr(service, 'default_model') and service.default_model in models:
                    self.model_combo.setCurrentText(service.default_model)
                    self.logger.info(f"设置默认模型: {service.default_model}")
                elif models:
                    self.model_combo.setCurrentText(models[0])
                    self.logger.info(f"设置第一个可用模型: {models[0]}")
                else:
                    self.logger.warning("没有可用的模型")
                    self.model_combo.setEnabled(False)

            except Exception as e:
                self.logger.error(f"获取模型列表失败: {str(e)}")
                self.model_combo.setEnabled(False)

            self.update_status("就绪")

        except Exception as e:
            error_msg = f"加载模型列表失败: {str(e)}"
            self.logger.error(error_msg)
            self.update_status(error_msg)
            # 显示错误对话框
            QMessageBox.critical(self, "错误", error_msg)

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
        elif event.key() == Qt.Key.Key_Tab:
            # 插入4个空格而不是制表符
            cursor = self.analysis_instruction.textCursor()
            cursor.insertText("    ")
            event.accept()
        else:
            # 调用原始的keyPressEvent
            super(QTextEdit, self.analysis_instruction).keyPressEvent(event)

    def handle_summary_key_press(self, event):
        """处理汇总指令输入框的按键事件"""
        if event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.generate_summary()
        elif event.key() == Qt.Key.Key_Tab:
            # 插入4个空格而不是制表符
            cursor = self.summary_instruction.textCursor()
            cursor.insertText("    ")
            event.accept()
        else:
            # 调用原始的keyPressEvent
            super(QTextEdit, self.summary_instruction).keyPressEvent(event)

    def select_directory(self):
        """选择目录"""
        dir_path = QFileDialog.getExistingDirectory(self, "选择目录")
        if dir_path:
            try:
                # 生成或更新文件索引
                self.current_directory = dir_path
                self.file_index = self.file_index_manager.generate_index(dir_path)

                # 清除旧的选择状态
                self.selected_files = []
                self.selected_files_display.setText(dir_path)
                self.logger.info(f"已选择目录: {dir_path}")
                self.update_status(f"已选择目录: {dir_path}")

                # 显示文件索引信息
                total_files = self.file_index["metadata"]["total_files"]
                QMessageBox.information(
                    self,
                    "目录索引",
                    f"目录索引已更新\n\n"
                    f"- 总文件数：{total_files}\n"
                    f"- 目录：{dir_path}"
                )

                # 清除其他状态
                self._clear_analysis_state()

            except Exception as e:
                self.logger.error(f"处理目录时发生错误: {str(e)}")
                QMessageBox.critical(self, "错误", f"处理目录时发生错误: {str(e)}")

    def _clear_analysis_state(self):
        """清除分析相关的状态"""
        self.analysis_results.clear()
        for i in reversed(range(self.result_layout.count())):
            widget = self.result_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.summary_display.clear()
        self.summary_button.setEnabled(False)
        self.save_button.setEnabled(False)
        self.analysis_count_label.setText("0/0")

    def handle_analysis_result(self, file_path: str, result: str):
        """处理分析结果"""
        try:
            # 更新文件的分析状态
            filename = os.path.basename(file_path)
            self.file_index_manager.update_analysis_status(self.current_directory, filename)

            # 保存结果
            self.analysis_results[file_path] = result
            self.logger.info(f"File analysis completed: {file_path}")

            # 显示结果
            result_window = AnalysisResultWindow(file_path)
            result_window.result_display.setText(result)
            self.result_layout.addWidget(result_window)

            # 更新进度条和计数
            current = len(self.analysis_results)
            total = len(self.selected_files)
            self.progress_bar.setValue(current)
            self.analysis_count_label.setText(f"{current}/{total}")

            # 更新状态信息
            progress_percentage = int((current / total) * 100)
            self.update_status(f"分析进度: {progress_percentage}% ({current}/{total})")

            # 检查是否所有文件都分析完成
            if current == total:
                self.progress_bar.setVisible(False)
                self.update_status("所有文件分析完成")
                self.logger.info("所有文件分析完成")

                # 启用汇总按钮，禁用其他按钮
                self.summary_button.setEnabled(True)
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.save_button.setEnabled(False)

                # 显示完成状态对话框
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setWindowTitle("分析完成")
                msg.setText("所有文件分析已完成")
                msg.setInformativeText(f"成功分析了 {current} 个文件")
                msg.setDetailedText("分析完成的文件列表：\n" + "\n".join(sorted(self.analysis_results.keys())))

                self.is_analyzing = False

        except Exception as e:
            self.logger.error(f"处理分析结果时发生错误: {str(e)}")
            self.handle_analysis_error(file_path, str(e))

    def handle_analysis_error(self, file_path: str, error: str):
        """处理分析错误"""
        try:
            self.logger.error(f"分析文件 {file_path} 时发生错误: {error}")
            self.update_status(f"分析文件 {file_path} 时发生错误")

            # 更新进度条
            current = self.progress_bar.value() + 1
            self.progress_bar.setValue(current)

            # 显示错误消息
            QMessageBox.warning(self, "错误", f"分析文件 {file_path} 时发生错误: {error}")

            # 检查是否所有文件都处理完成
            if current == len(self.selected_files):
                self.progress_bar.setVisible(False)
                self.is_analyzing = False
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)

        except Exception as e:
            self.logger.error(f"处理分析错误时发生异常: {str(e)}")
            QMessageBox.critical(self, "错误", f"处理分析错误时发生异常: {str(e)}")

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
                filename = os.path.basename(file_path)
                file_info = {
                    "file_path": file_path,
                    "directory": os.path.dirname(file_path),
                    "filename": filename,
                    "analysis_result": content,
                    "global_index": self.file_index["files"][filename]["index"],
                    "batch_index": len(summary_data) + 1
                }
                summary_data.append(file_info)

            # 更新文件的汇总状态
            summary_id = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.file_index_manager.update_summary_status(
                self.current_directory,
                [item["filename"] for item in summary_data],
                summary_id
            )

            # 创建新的汇总线程
            self.summary_thread = SummaryThread(
                summary_data,
                self.ai_services[self.current_service],
                instruction
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

            # 隐藏进度条
            self.progress_bar.setVisible(False)

            # 显示汇总结果
            self.summary_display.setText(result)
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
                f"汇总报告已生成完成\n\n已成功汇总 {len(self.analysis_results)} 个文件的分析结果。"
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

    def handle_summary_error(self, error: str):
        """处理汇总错误"""
        self.logger.error(f"汇总报告生成失败: {error}")
        self.update_status("汇总报告生成失败")
        QMessageBox.warning(self, "错误", f"生成汇总报告时发生错误: {error}")

        # 清理线程
        if hasattr(self, 'summary_thread') and self.summary_thread is not None:
            self.logger.info("清理汇总线程")
            if self.summary_thread.is_running:
                self.summary_thread.wait()
            self.summary_thread.deleteLater()
            self.summary_thread = None
            self.logger.info("汇总线程已清理")

    def save_summary(self):
        """保存汇总报告到markdown文件"""
        if not self.summary_display.toPlainText():
            self.logger.warning("没有可保存的汇总内容")
            QMessageBox.warning(self, "警告", "没有可保存的汇总内容")
            return

        try:
            # 获取当前时间作为文件名的一部分
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"summary_report_{timestamp}.md"

            # 打开文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "保存汇总报告",
                default_filename,
                "Markdown文件 (*.md);;所有文件 (*.*)"
            )

            if file_path:
                # 确保文件扩展名为.md
                if not file_path.lower().endswith('.md'):
                    file_path += '.md'

                # 写入文件
                with open(file_path, 'w', encoding='utf-8') as f:
                    # 添加标题和时间戳
                    f.write(f"# 论文分析汇总报告\n\n")
                    f.write(f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("---\n\n")
                    # 写入汇总内容
                    f.write(self.summary_display.toPlainText())

                self.logger.info(f"汇总报告已保存到: {file_path}")
                self.update_status(f"汇总报告已保存到: {file_path}")
                QMessageBox.information(self, "成功", "汇总报告已成功保存")

        except Exception as e:
            self.logger.error(f"保存汇总报告时出错: {str(e)}")
            self.update_status("保存汇总报告失败")
            QMessageBox.critical(self, "错误", f"保存汇总报告时出错: {str(e)}")

    def save_prompt(self, prompt_type: str):
        """保存提示词
        
        Args:
            prompt_type: 提示词类型 ('analysis' 或 'summary')
        """
        try:
            # 获取当前文本
            text = (self.analysis_instruction.toPlainText()
                    if prompt_type == 'analysis'
                    else self.summary_instruction.toPlainText())

            if not text.strip():
                QMessageBox.warning(self, "警告", "提示词不能为空")
                return

            # 确认是否保存
            reply = QMessageBox.question(
                self,
                "确认保存",
                f"确定要将当前{prompt_type}提示词保存为自定义提示词吗？\n这将覆盖已有的自定义提示词。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                if self.prompt_manager.save_custom_prompt(prompt_type, text):
                    QMessageBox.information(
                        self,
                        "成功",
                        f"已成功保存{prompt_type}提示词\n\n提示：下次启动时将优先使用此自定义提示词"
                    )
                    self.logger.info(f"已保存{prompt_type}自定义提示词")
                else:
                    QMessageBox.warning(self, "警告", f"保存{prompt_type}提示词失败")

        except Exception as e:
            self.logger.error(f"保存{prompt_type}提示词失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"保存提示词失败: {str(e)}")

    def reset_prompt(self, prompt_type: str):
        """重置提示词为默认值
        
        Args:
            prompt_type: 提示词类型 ('analysis' 或 'summary')
        """
        try:
            # 确认对话框
            reply = QMessageBox.question(
                self,
                "确认重置",
                f"确定要将{prompt_type}提示词重置为默认值吗？\n这将删除已保存的自定义提示词。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                if self.prompt_manager.reset_custom_prompt(prompt_type):
                    # 获取重置后的提示词
                    default_text = self.prompt_manager.get_prompt(prompt_type)

                    # 更新文本编辑器内容
                    if prompt_type == 'analysis':
                        self.analysis_instruction.setPlainText(default_text or "")
                    else:
                        self.summary_instruction.setPlainText(default_text or "")

                    QMessageBox.information(
                        self,
                        "成功",
                        f"已重置{prompt_type}提示词为默认值\n\n提示：下次启动时将使用默认提示词"
                    )
                    self.logger.info(f"已重置{prompt_type}提示词为默认值")
                else:
                    QMessageBox.warning(self, "警告", f"重置{prompt_type}提示词失败")

        except Exception as e:
            self.logger.error(f"重置{prompt_type}提示词失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"重置提示词失败: {str(e)}")

    def reset_ui_state(self):
        """重置UI状态"""
        self.progress_bar.setVisible(False)
        self.summary_button.setEnabled(bool(self.analysis_results))
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.save_button.setEnabled(bool(self.summary_display.toPlainText()))
        self.update_status("就绪")

    def _has_unsaved_changes(self, prompt_type: str) -> bool:
        """检查指令是否有未保存的更改
        
        Args:
            prompt_type: 指令类型 ('analysis' 或 'summary')
            
        Returns:
            bool: 是否有未保存的更改
        """
        try:
            # 获取当前文本
            current_text = (self.analysis_instruction.toPlainText()
                            if prompt_type == 'analysis'
                            else self.summary_instruction.toPlainText())

            # 获取已保存的提示词
            saved_prompt = self.prompt_manager.get_prompt(prompt_type, use_custom=True)

            # 比较当前文本和保存的提示词
            return current_text.strip() != (saved_prompt or "").strip()

        except Exception as e:
            self.logger.error(f"检查{prompt_type}提示词更改状态时发生错误: {str(e)}")
            return False

    def _update_prompt_status(self, prompt_type: str):
        """更新提示词状态显示
        
        Args:
            prompt_type: 指令类型 ('analysis' 或 'summary')
        """
        try:
            # 获取状态标签
            status_label = (self.analysis_status_label
                            if prompt_type == 'analysis'
                            else self.summary_status_label)

            # 检查是否有自定义提示词
            has_custom = bool(self.prompt_manager.prompts[prompt_type]['custom'])

            # 检查是否有未保存的更改
            has_unsaved = self._has_unsaved_changes(prompt_type)

            # 更新状态文本和样式
            if has_custom:
                status_text = "当前：自定义提示词"
                if has_unsaved:
                    status_text += " (有未保存的更改)"
                    status_style = """
                        QLabel {
                            color: #dc3545;
                            font-style: italic;
                        }
                    """
                else:
                    status_style = """
                        QLabel {
                            color: #28a745;
                        }
                    """
            else:
                status_text = "当前：默认提示词"
                if has_unsaved:
                    status_text += " (有未保存的更改)"
                    status_style = """
                        QLabel {
                            color: #dc3545;
                            font-style: italic;
                        }
                    """

            status_label.setText(status_text)
            status_label.setStyleSheet(status_style)

        except Exception as e:
            self.logger.error(f"更新{prompt_type}提示词状态显示时发生错误: {str(e)}")

    def show_file_selection_dialog(self):
        """显示文件选择对话框"""
        try:
            # 检查是否已选择目录
            if not self.current_directory or not self.file_index:
                self.logger.warning("未选择目录")
                QMessageBox.warning(self, "警告", "请先选择一个目录")
                return

            # 创建文件选择对话框
            dialog = FileSelectionDialog(
                parent=self,
                directory=self.current_directory,
                file_index=self.file_index,
                selected_files=self.selected_files,
                title="选择要分析的文件"
            )

            # 显示对话框并处理结果
            if dialog.exec() == QDialog.DialogCode.Accepted:
                # 获取选中的文件
                self.selected_files = dialog.get_selected_files()
                # 更新显示
                self.update_selected_files_display()
                self.logger.info(f"已选择 {len(self.selected_files)} 个文件")

        except Exception as e:
            self.logger.error(f"显示文件选择对话框时发生错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"显示文件选择对话框时发生错误: {str(e)}")

    def generate_file_summary_table(self):
        """生成文件汇总表格，包含目录下所有文件"""
        try:
            if not self.current_directory or not self.file_index:
                self.logger.warning("未选择目录")
                return

            # 获取目录下所有文件
            all_files = []
            for filename, file_info in self.file_index["files"].items():
                file_path = os.path.join(self.current_directory, filename)
                try:
                    # 获取文件大小（以MB为单位）
                    file_size = os.path.getsize(file_path) / (1024 * 1024)
                    file_info['size_mb'] = round(file_size, 2)
                    file_info['file_path'] = file_path
                    all_files.append(file_info)
                except Exception as e:
                    self.logger.error(f"获取文件{filename}大小时出错: {str(e)}")
                    continue

            # 按文件索引排序
            all_files.sort(key=lambda x: x['index'])

            # 生成表格内容
            table_content = [
                "# 文件汇总表格\n\n",
                f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
                f"目录：{self.current_directory}\n",
                f"总文件数：{len(all_files)}\n",
                f"选中文件数：{len(self.selected_files)}\n\n",
                "| 序号 | 文件名 | 大小(MB) | 状态 | 分析次数 | 最后分析时间 | 汇总状态 |",
                "|------|--------|-----------|--------|----------|--------------|----------|"
            ]

            # 添加文件信息
            for file_info in all_files:
                filename = os.path.basename(file_info['file_path'])
                file_path = file_info['file_path']

                # 确定文件状态
                status = []
                if file_info['size_mb'] > 30:
                    status.append("⚠️超大文件")
                if file_path in self.selected_files:
                    status.append("✅已选择")
                status = ", ".join(status) if status else "未选择"

                # 格式化时间
                last_analysis_time = file_info.get("last_analysis_time", "未分析")
                if last_analysis_time != "未分析":
                    try:
                        last_analysis_time = datetime.fromisoformat(last_analysis_time).strftime("%Y-%m-%d %H:%M:%S")
                    except:
                        pass

                # 获取汇总状态
                summary_status = "未汇总"
                if "summary_status" in file_info:
                    summary_status = f"已汇总 ({file_info['summary_status']})"

                # 添加表格行
                table_content.append(
                    f"| {file_info['index']:04d} | {filename} | {file_info['size_mb']:.2f} | "
                    f"{status} | {file_info['analysis_count']} | {last_analysis_time} | {summary_status} |"
                )

            # 保存到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            summary_dir = os.path.join(self.current_directory, "summaries")
            os.makedirs(summary_dir, exist_ok=True)

            file_path = os.path.join(summary_dir, f"file_summary_{timestamp}.md")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(table_content))

            self.logger.info(f"文件汇总表格已保存到: {file_path}")
            self.update_status(f"文件汇总表格已生成: {file_path}")

            # 显示成功消息
            QMessageBox.information(
                self,
                "文件汇总表格已生成",
                f"文件汇总表格已保存到:\n{file_path}\n\n"
                f"共包含 {len(all_files)} 个文件的信息\n"
                f"其中 {len(self.selected_files)} 个文件被选中进行分析"
            )

            return all_files  # 返回所有文件信息，供其他函数使用

        except Exception as e:
            self.logger.error(f"生成文件汇总表格时发生错误: {str(e)}")
            QMessageBox.warning(self, "警告", f"生成文件汇总表格时发生错误: {str(e)}")
            return None

    def start_analysis(self):
        """开始分析"""
        try:
            # 检查是否选择了文件
            if not self.selected_files:
                self.logger.warning("未选择任何文件")
                QMessageBox.warning(self, "警告", "请先选择要分析的文件")
                return

            # 获取分析指令
            instruction = self.analysis_instruction.toPlainText().strip()
            if not instruction:
                instruction = self.prompt_manager.get_prompt('analysis') or ""
                if not instruction:
                    QMessageBox.warning(self, "警告", "分析指令不能为空")
                    return

            # 先生成文件汇总表格，并获取所有文件信息
            all_files = self.generate_file_summary_table()
            if not all_files:
                return

            # 过滤出要分析的文件（排除大于30MB的文件）
            files_to_analyze = []
            skipped_files = []

            for file_info in all_files:
                file_path = file_info['file_path']
                if file_path not in self.selected_files:
                    continue

                if file_info['size_mb'] > 30:
                    skipped_files.append((file_path, file_info['size_mb']))
                else:
                    files_to_analyze.append(file_path)

            # 如果有被跳过的文件，显示提示
            if skipped_files:
                skip_msg = "以下文件因大于30MB而被跳过：\n\n"
                for file_path, size in skipped_files:
                    skip_msg += f"- {os.path.basename(file_path)} ({size:.2f}MB)\n"
                QMessageBox.warning(self, "文件跳过提示", skip_msg)

            if not files_to_analyze:
                QMessageBox.warning(self, "警告", "没有可分析的文件（所有选中的文件都超过30MB）")
                return

            # 清除旧的分析结果
            self.analysis_results.clear()

            # 清除UI中的旧结果显示
            for i in reversed(range(self.result_layout.count())):
                widget = self.result_layout.itemAt(i).widget()
                if widget is not None:
                    widget.deleteLater()

            # 重置进度条和计数
            self.progress_bar.setMaximum(len(files_to_analyze))
            self.progress_bar.setValue(0)
            self.progress_bar.setVisible(True)
            self.analysis_count_label.setText(f"0/{len(files_to_analyze)}")

            # 禁用汇总和保存按钮
            self.summary_button.setEnabled(False)
            self.save_button.setEnabled(False)

            # 设置分析状态
            self.is_analyzing = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)

            # 创建并启动分析线程
            self.analysis_threads.clear()

            # 按文件索引顺序排序文件
            sorted_files = sorted(
                files_to_analyze,
                key=lambda x: self.file_index["files"][os.path.basename(x)]["index"]
            )

            for file_path in sorted_files:
                thread = AnalysisThread(file_path, self.ai_services[self.current_service], instruction)
                thread.analysis_completed.connect(self.handle_analysis_result)
                thread.error_occurred.connect(self.handle_analysis_error)
                thread.status_updated.connect(self.update_status)
                self.analysis_threads.append(thread)
                thread.start()

            self.logger.info(f"开始分析 {len(files_to_analyze)} 个PDF文件")
            self.update_status(f"开始分析 {len(files_to_analyze)} 个PDF文件...")

        except Exception as e:
            self.logger.error(f"启动分析时发生错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"启动分析时发生错误: {str(e)}")
            self.is_analyzing = False
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)
            self.progress_bar.setVisible(False)

    def stop_analysis(self):
        """停止分析"""
        try:
            if not self.is_analyzing:
                self.logger.warning("当前没有正在进行的分析")
                return

            # 确认是否停止
            reply = QMessageBox.question(
                self,
                "确认停止",
                "确定要停止当前的分析吗？\n已完成的分析结果将被保留。",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.logger.info("用户确认停止分析")

                # 停止所有分析线程
                for thread in self.analysis_threads:
                    if thread.isRunning():
                        self.logger.info(f"正在停止线程: {thread}")
                        thread.terminate()
                        thread.wait()

                # 清理线程列表
                self.analysis_threads.clear()

                # 更新UI状态
                self.is_analyzing = False
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.progress_bar.setVisible(False)

                # 如果有分析结果，启用汇总按钮
                if self.analysis_results:
                    self.summary_button.setEnabled(True)

                self.update_status("分析已停止")

                # 显示停止信息
                QMessageBox.information(
                    self,
                    "已停止",
                    f"分析已停止\n\n已完成 {len(self.analysis_results)} 个文件的分析"
                )

        except Exception as e:
            self.logger.error(f"停止分析时发生错误: {str(e)}")
            QMessageBox.critical(self, "错误", f"停止分析时发生错误: {str(e)}")

    def update_selected_files_display(self):
        """更新已选择文件的显示"""
        try:
            if not self.selected_files:
                self.selected_files_display.setText("未选择任何文件")
                return

            # 获取目录路径和文件名
            dir_path = os.path.dirname(self.selected_files[0])
            file_names = []

            # 按文件索引排序
            sorted_files = sorted(
                self.selected_files,
                key=lambda x: self.file_index["files"][os.path.basename(x)]["index"]
            )

            # 生成显示文本
            for file_path in sorted_files:
                filename = os.path.basename(file_path)
                file_index = self.file_index["files"][filename]["index"]
                analysis_count = self.file_index["files"][filename]["analysis_count"]

                # 格式化显示文本
                display_text = f"{file_index:04d}. {filename}"
                if analysis_count > 0:
                    display_text += f" (已分析: {analysis_count}次)"
                file_names.append(display_text)

            # 组合显示文本
            display_text = f"目录: {dir_path}\n"
            display_text += f"已选择 {len(file_names)} 个文件:\n"
            display_text += "\n".join(file_names)

            # 更新显示
            self.selected_files_display.setText(display_text)
            self.logger.info(f"已更新文件选择显示，选中了 {len(file_names)} 个文件")

            # 启用开始分析按钮
            self.start_button.setEnabled(True)

        except Exception as e:
            self.logger.error(f"更新文件选择显示时发生错误: {str(e)}")
            self.selected_files_display.setText("更新文件显示时发生错误")

    def setup_progress_bar_style(self):
        """设置进度条样式"""
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 3px;
                text-align: center;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4CAF50;
                border-radius: 2px;
            }
        """)

    def fix_styles(self):
        """修复样式"""
        # 修复进度条样式
        self.setup_progress_bar_style()

        # 修复其他组件样式
        for widget in self.findChildren(QWidget):
            if widget.styleSheet() and "box-shadow" in widget.styleSheet():
                # 移除box-shadow相关样式
                style = widget.styleSheet()
                style = '\n'.join([line for line in style.split('\n')
                                   if 'box-shadow' not in line])
                widget.setStyleSheet(style)

                # 添加边框效果
                widget.setStyleSheet(widget.styleSheet() + """
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    background-color: white;
                """)
