from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QLineEdit, QPushButton, QLabel, QStatusBar,
                            QFileDialog, QScrollArea, QFrame, QComboBox,
                            QDialog, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QImage
from utils.logger import Logger
from utils.version import version_info
from services.message_types import Message, ChatHistory
from services.openai_service import OpenAIService
from services.grok_service import GrokService
from utils.config_manager import ConfigManager
import os
import base64
from PIL import Image
import io
import logging


class FilePreviewWidget(QFrame):
    """文件预览组件"""
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 文件名标签
        file_name = os.path.basename(self.file_path)
        name_label = QLabel(file_name)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)
        
        # 预览区域
        preview_label = QLabel()
        preview_label.setFixedSize(100, 100)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 根据文件类型显示不同的预览
        if self.file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            pixmap = QPixmap(self.file_path)
            scaled_pixmap = pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio)
            preview_label.setPixmap(scaled_pixmap)
        else:
            preview_label.setText("文件")
            
        layout.addWidget(preview_label)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setFixedWidth(60)
        delete_btn.clicked.connect(self.deleteLater)
        layout.addWidget(delete_btn)
        
        self.setLayout(layout)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setFixedSize(120, 180)


"""
类似ChatGPT的聊天功能
"""
class ChatForm(QWidget):
    def __init__(self):
        super().__init__()
        config_manager = ConfigManager()
        global_config = config_manager.get_config()
        log_level = global_config.get('logging.level', 'INFO')
        self.logger = Logger.create_logger('chat')
        self.chat_history = ChatHistory()
        self.attached_files = []  # 存储已上传的文件路径
        
        # 初始化配置管理器
        config_manager = ConfigManager()

        # 初始化AI服务
        self.ai_services = {
            "OpenAI": OpenAIService(config_manager=config_manager),
            "Grok": GrokService(config_manager=config_manager)
        }
        self.current_service = "OpenAI"  # 默认使用OpenAI
        
        self.init_ui()
        self.load_models()

    def init_ui(self):
        """初始化UI布局"""
        self.setWindowTitle('AI对话')
        layout = QVBoxLayout()

        # 服务选择区域
        service_layout = QHBoxLayout()
        service_label = QLabel("AI服务:")
        self.service_combo = QComboBox()
        self.service_combo.addItems(self.ai_services.keys())
        self.service_combo.currentTextChanged.connect(self.on_service_changed)
        service_layout.addWidget(service_label)
        service_layout.addWidget(self.service_combo)
        layout.addLayout(service_layout)

        # 提供商选择区域
        ai_service = self.ai_services[self.current_service]
        providers = ai_service.get_providers()
        provider_layout = QHBoxLayout()
        provider_label = QLabel("提供商:")
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(providers)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(self.provider_combo)
        layout.addLayout(provider_layout)

        # 模型选择区域
        model_layout = QHBoxLayout()
        model_label = QLabel("AI模型:")
        self.model_combo = QComboBox()
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        
        # 添加关于按钮
        about_button = QPushButton("关于")
        about_button.clicked.connect(self.show_about_dialog)
        model_layout.addWidget(about_button)
        
        layout.addLayout(model_layout)

        # 对话历史显示区域
        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        layout.addWidget(self.history_display)

        # 输入区域
        input_layout = QVBoxLayout()
        
        # 文件预览区域
        preview_scroll = QScrollArea()
        preview_scroll.setWidgetResizable(True)
        preview_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        preview_scroll.setFixedHeight(200)
        
        self.preview_container = QWidget()
        self.preview_layout = QHBoxLayout(self.preview_container)
        self.preview_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        preview_scroll.setWidget(self.preview_container)
        
        input_layout.addWidget(preview_scroll)
        
        # 消息输入区域
        message_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.returnPressed.connect(self.send_message)
        
        # 文件上传按钮
        self.upload_button = QPushButton()
        self.upload_button.setIcon(QIcon("icons/upload.png"))  # 需要添加图标文件
        self.upload_button.setIconSize(QSize(24, 24))
        self.upload_button.setFixedSize(40, 40)
        self.upload_button.clicked.connect(self.upload_file)
        
        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.clicked.connect(self.send_message)
        
        message_layout.addWidget(self.message_input)
        message_layout.addWidget(self.upload_button)
        message_layout.addWidget(self.send_button)
        input_layout.addLayout(message_layout)
        
        layout.addLayout(input_layout)

        # 状态栏
        self.status_bar = QStatusBar()
        self.status_bar.showMessage("就绪")
        layout.addWidget(self.status_bar)

        self.setLayout(layout)

    def load_models(self):
        """加载可用的AI模型"""
        try:
            self.status_bar.showMessage("正在加载模型列表...")
            # 获取当前服务和提供商的可用模型
            service = self.service_combo.currentText()
            provider = self.provider_combo.currentText()
            models = self.ai_services[service].get_models()
            
            # 更新下拉框
            self.model_combo.clear()
            self.model_combo.addItems(models)
            
            # 设置默认模型
            if models:
                self.model_combo.setCurrentText(models[0])
            
            self.status_bar.showMessage("就绪")
        except Exception as e:
            self.logger.error(f"加载模型列表失败: {str(e)}")
            self.status_bar.showMessage(f"加载模型失败: {str(e)}")

    def on_model_changed(self, model_name: str):
        """处理模型选择变化"""
        try:
            self.status_bar.showMessage(f"正在切换到模型: {model_name}")
            # 更新当前服务使用的模型
            self.ai_services[self.current_service].model = model_name
            self.status_bar.showMessage("就绪")
        except Exception as e:
            self.logger.error(f"切换模型失败: {str(e)}")
            self.status_bar.showMessage(f"切换模型失败: {str(e)}")

    def upload_file(self):
        """处理文件上传"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "选择文件",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp);;所有文件 (*.*)"
        )
        
        if file_path:
            self.attached_files.append(file_path)
            preview = FilePreviewWidget(file_path)
            self.preview_layout.addWidget(preview)
            self.logger.info(f"文件已上传: {file_path}")

    def send_message(self):
        """发送消息并获取AI回复"""
        message_text = self.message_input.text().strip()
        if not message_text and not self.attached_files:
            return

        # 创建用户消息
        user_message = Message(role="user", content=message_text)
        
        # 处理附件
        if self.attached_files:
            attachments = []
            for file_path in self.attached_files:
                try:
                    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                        # 处理图片文件
                        with Image.open(file_path) as img:
                            # 调整图片大小
                            max_size = (800, 800)
                            img.thumbnail(max_size)
                            # 转换为base64
                            buffered = io.BytesIO()
                            img.save(buffered, format="PNG")
                            img_str = base64.b64encode(buffered.getvalue()).decode()
                            attachments.append({
                                "type": "image",
                                "data": img_str,
                                "name": os.path.basename(file_path)
                            })
                    else:
                        # 处理文本文件
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            attachments.append({
                                "type": "text",
                                "data": content,
                                "name": os.path.basename(file_path)
                            })
                except Exception as e:
                    self.logger.error(f"处理文件失败: {str(e)}")
                    continue
            
            if attachments:
                user_message.attachments = attachments

        self.chat_history.add_message(user_message)
        self.update_display()

        # 清空输入框和附件
        self.message_input.clear()
        self.clear_attachments()

        try:
            # 获取AI回复
            self.status_bar.showMessage("正在获取回复...")
            response = self.ai_services[self.current_service].send_message(self.chat_history.get_messages())
            
            # 将响应转换为Message对象
            if isinstance(response, dict):
                ai_message = Message(
                    role="assistant",
                    content=response["choices"][0]["message"]["content"]
                )
            else:
                # 如果response已经是Message对象，直接使用
                ai_message = response
                
            self.chat_history.add_message(ai_message)
            self.update_display()
            self.status_bar.showMessage("就绪")
        except Exception as e:
            self.logger.error(f"发送消息失败: {str(e)}")
            self.status_bar.showMessage(f"错误: {str(e)}")

    def clear_attachments(self):
        """清除所有附件"""
        self.attached_files.clear()
        # 清除预览区域的所有组件
        while self.preview_layout.count():
            item = self.preview_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def update_display(self):
        """更新对话显示"""
        self.history_display.clear()
        for message in self.chat_history.get_messages():
            role_prefix = "用户: " if message.role == "user" else "AI: "
            content = f"{role_prefix}{message.content}\n"
            
            # 显示附件信息
            if hasattr(message, 'attachments') and message.attachments:
                content += "附件:\n"
                for attachment in message.attachments:
                    content += f"- {attachment['name']}\n"
            
            self.history_display.append(content)
            
        # 滚动到底部
        self.history_display.verticalScrollBar().setValue(
            self.history_display.verticalScrollBar().maximum()
        )

    def show_about_dialog(self):
        """显示关于对话框"""
        about_text = f"""
        <h2>AI对话工具</h2>
        <p>版本: {version_info.version}</p>
        <p>发布日期: {version_info.release_date}</p>
        <p>作者: {version_info.author}</p>
        <p>邮箱: {version_info.email}</p>
        <p>许可证: {version_info.license}</p>
        
        <h3>更新说明</h3>
        <pre>{version_info.changelog}</pre>
        
        <h3>依赖要求</h3>
        <pre>{version_info.requirements}</pre>
        """
        
        QMessageBox.about(self, "关于", about_text)

    def on_service_changed(self, service_name: str):
        """处理服务选择变化"""
        try:
            self.status_bar.showMessage(f"正在切换到服务: {service_name}")
            # 更新提供商列表
            providers = self.ai_services[service_name].get_providers()
            self.provider_combo.clear()
            self.provider_combo.addItems(providers)
            self.load_models()
            self.status_bar.showMessage("就绪")
        except Exception as e:
            self.logger.error(f"切换服务失败: {str(e)}")
            self.status_bar.showMessage(f"切换服务失败: {str(e)}")
        

    def on_provider_changed(self, provider_name: str):
        """处理提供商选择变化"""
        try:
            self.logger.info(f"正在切换到提供商: {provider_name}")
            self.status_bar.showMessage(f"正在切换到提供商: {provider_name}")
            self.ai_services[self.current_service].provider = provider_name
            self.load_models()
            self.status_bar.showMessage("就绪")
        except Exception as e:
            self.logger.error(f"切换提供商失败: {str(e)}")
            self.status_bar.showMessage(f"切换提供商失败: {str(e)}")
