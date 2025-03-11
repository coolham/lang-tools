from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QLineEdit, QPushButton, QLabel, QStatusBar,
                            QFileDialog, QScrollArea, QFrame, QComboBox,
                            QDialog, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QImage, QKeySequence, QShortcut, QFont
from utils.logger import Logger
from utils.version import version_info
from services.message_types import Message, ChatHistory
from services.openai_service import OpenAIService
from services.grok_service import GrokService
from utils.config_manager import ConfigManager
from widgets.file_preview_widget import FilePreviewWidget
import os
import base64
from PIL import Image
import io
import logging


"""
类似ChatGPT的聊天功能
"""
class ChatForm(QWidget):
    def __init__(self):
        super().__init__()
        self.init_config()
        self.chat_history = ChatHistory()
        self.attached_files = []  # 存储已上传的文件路径
        
        self.init_ai_services()
        self.init_ui()
        self.load_models()
        self.init_message_styles()
        self.message_cache = MessageCache()
        self.setup_shortcuts()

    def init_config(self):
        self.config_manager = ConfigManager()
        self.global_config = self.config_manager.get_config()
        self.log_level = self.global_config.get('logging.level', 'INFO')
        self.logger = Logger.create_logger('chat')

    def init_ai_services(self):
        self.ai_services = {
            "OpenAI": OpenAIService(config_manager=self.config_manager),
            "Grok": GrokService(config_manager=self.config_manager)
        }
        self.current_service = "OpenAI"

    def init_ui(self):
        """初始化UI布局"""
        self.setWindowTitle('AI对话')
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # 服务选择区域
        service_layout = QHBoxLayout()
        service_label = QLabel("AI服务:")
        service_label.setFont(QFont("Microsoft YaHei", 10))
        self.service_combo = QComboBox()
        self.service_combo.setFont(QFont("Microsoft YaHei", 10))
        self.service_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                padding: 5px;
                min-width: 100px;
            }
            QComboBox:hover {
                border: 1px solid #1890ff;
            }
        """)
        self.service_combo.addItems(self.ai_services.keys())
        self.service_combo.currentTextChanged.connect(self.on_service_changed)
        service_layout.addWidget(service_label)
        service_layout.addWidget(self.service_combo)
        service_layout.addStretch()
        layout.addLayout(service_layout)

        # 提供商选择区域
        provider_layout = QHBoxLayout()
        provider_label = QLabel("提供商:")
        provider_label.setFont(QFont("Microsoft YaHei", 10))
        self.provider_combo = QComboBox()
        self.provider_combo.setFont(QFont("Microsoft YaHei", 10))
        self.provider_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                padding: 5px;
                min-width: 100px;
            }
            QComboBox:hover {
                border: 1px solid #1890ff;
            }
        """)
        ai_service = self.ai_services[self.current_service]
        providers = ai_service.get_providers()
        self.provider_combo.addItems(providers)
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        provider_layout.addWidget(provider_label)
        provider_layout.addWidget(self.provider_combo)
        provider_layout.addStretch()
        layout.addLayout(provider_layout)

        # 模型选择区域
        model_layout = QHBoxLayout()
        model_label = QLabel("AI模型:")
        model_label.setFont(QFont("Microsoft YaHei", 10))
        self.model_combo = QComboBox()
        self.model_combo.setFont(QFont("Microsoft YaHei", 10))
        self.model_combo.setStyleSheet("""
            QComboBox {
                border: 1px solid #dcdcdc;
                border-radius: 4px;
                padding: 5px;
                min-width: 100px;
            }
            QComboBox:hover {
                border: 1px solid #1890ff;
            }
        """)
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        
        # 添加关于按钮
        about_button = QPushButton("关于")
        about_button.setFont(QFont("Microsoft YaHei", 10))
        about_button.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                border-radius: 4px;
                padding: 5px 15px;
                color: #333333;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        about_button.clicked.connect(self.show_about_dialog)
        model_layout.addWidget(about_button)
        
        layout.addLayout(model_layout)

        # 对话历史显示区域
        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setFont(QFont("Microsoft YaHei", 10))
        self.history_display.setStyleSheet("""
            QTextEdit {
                border: 1px solid #dcdcdc;
                border-radius: 8px;
                padding: 10px;
                background-color: white;
            }
        """)
        layout.addWidget(self.history_display)

        # 输入区域
        input_layout = QVBoxLayout()
        
        # 文件预览区域
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.preview_scroll.setFixedHeight(200)
        self.preview_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
        """)
        self.preview_scroll.setVisible(False)  # 初始时隐藏预览区域
        
        self.preview_container = QWidget()
        self.preview_layout = QHBoxLayout(self.preview_container)
        self.preview_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.preview_layout.setContentsMargins(0, 0, 0, 0)
        self.preview_scroll.setWidget(self.preview_container)
        
        input_layout.addWidget(self.preview_scroll)
        
        # 消息输入区域
        message_layout = QHBoxLayout()
        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("输入消息...")
        self.message_input.setFont(QFont("Microsoft YaHei", 10))
        self.message_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #dcdcdc;
                border-radius: 20px;
                padding: 10px 15px;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #1890ff;
            }
        """)
        self.message_input.returnPressed.connect(self.send_message)
        
        # 文件上传按钮
        self.upload_button = QPushButton()
        self.upload_button.setIcon(QIcon("icons/upload.png"))
        self.upload_button.setIconSize(QSize(20, 20))
        self.upload_button.setFixedSize(40, 40)
        self.upload_button.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                border: none;
                border-radius: 20px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:pressed {
                background-color: #096dd9;
            }
        """)
        self.upload_button.clicked.connect(self.upload_file)
        
        # 发送按钮
        self.send_button = QPushButton("发送")
        self.send_button.setFont(QFont("Microsoft YaHei", 10))
        self.send_button.setFixedSize(80, 40)
        self.send_button.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 20px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
            QPushButton:disabled {
                background-color: #bae7ff;
            }
        """)
        self.send_button.clicked.connect(self.send_message)
        
        message_layout.addWidget(self.message_input)
        message_layout.addWidget(self.upload_button)
        message_layout.addWidget(self.send_button)
        input_layout.addLayout(message_layout)
        
        layout.addLayout(input_layout)

        # 状态栏
        self.status_bar = QStatusBar()
        self.status_bar.setFont(QFont("Microsoft YaHei", 9))
        self.status_bar.setStyleSheet("""
            QStatusBar {
                border-top: 1px solid #dcdcdc;
                padding: 5px;
                color: #666666;
            }
        """)
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

    def is_valid_file_type(self, file_path: str) -> bool:
        valid_extensions = {
            'image': ['.png', '.jpg', '.jpeg', '.gif', '.bmp'],
            'text': ['.txt', '.md', '.py', '.js', '.html']
        }
        ext = os.path.splitext(file_path)[1].lower()
        return any(ext in exts for exts in valid_extensions.values())

    def upload_file(self):
        """处理文件上传"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "选择文件",
            "",
            "图片文件 (*.png *.jpg *.jpeg *.gif *.bmp);;文本文件 (*.txt *.md *.py *.js *.html);;所有文件 (*.*)"
        )
        
        if file_path:
            if not self.is_valid_file_type(file_path):
                QMessageBox.warning(self, "警告", "不支持的文件类型")
                return
            
            # 如果是第一个文件，显示预览区域
            if not self.attached_files:
                self.preview_scroll.setVisible(True)
            
            self.attached_files.append(file_path)
            preview = FilePreviewWidget(file_path)
            self.preview_layout.addWidget(preview)
            self.logger.info(f"文件已上传: {file_path}")

    def handle_errors(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                self.logger.error(f"{func.__name__} 执行失败: {str(e)}")
                self.status_bar.showMessage(f"错误: {str(e)}")
                return None
        return wrapper

    @handle_errors
    def send_message(self):
        """发送消息并获取AI回复"""
        if not self.message_input.text().strip() and not self.attached_files:
            return
        
        self.set_loading_state(True)
        try:
            # 创建用户消息
            message_text = self.message_input.text().strip()
            if not message_text and self.attached_files:
                message_text = "请描述这张图片"  # 如果只有图片没有文字，添加默认提示文本
            
            user_message = Message(role="user", content=message_text)
            
            # 处理附件
            if self.attached_files:
                attachments = []
                for file_path in self.attached_files:
                    try:
                        if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                            # 处理图片文件
                            with Image.open(file_path) as img:
                                # 转换为RGB模式（如果是RGBA，移除alpha通道）
                                if img.mode in ('RGBA', 'LA'):
                                    background = Image.new('RGB', img.size, (255, 255, 255))
                                    background.paste(img, mask=img.split()[-1])
                                    img = background
                                elif img.mode != 'RGB':
                                    img = img.convert('RGB')
                                
                                # 调整图片大小，确保不超过API限制
                                max_size = (2000, 2000)  # OpenAI API 建议的最大尺寸
                                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                                
                                # 转换为base64
                                buffered = io.BytesIO()
                                img.save(buffered, format="JPEG", quality=95)  # 使用JPEG格式，设置较高的质量
                                img_str = base64.b64encode(buffered.getvalue()).decode()
                                
                                # 添加正确的mime type前缀
                                img_base64 = f"data:image/jpeg;base64,{img_str}"
                                
                                attachments.append({
                                    "type": "image",
                                    "data": img_base64,
                                    "name": os.path.basename(file_path)
                                })
                                
                                self.logger.info(f"成功处理图片: {file_path}")
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
                        self.logger.error(f"处理文件失败 {file_path}: {str(e)}")
                        continue
                
                if attachments:
                    user_message.attachments = attachments
                    self.logger.info(f"添加了 {len(attachments)} 个附件到消息中")

            self.chat_history.add_message(user_message)
            self.update_display()

            # 清空输入框和附件
            self.message_input.clear()
            self.clear_attachments()

            # 获取AI回复
            self.logger.info("正在发送消息到AI服务...")
            response = self.ai_services[self.current_service].send_message(self.chat_history.get_messages())
            self.logger.info("收到AI服务响应")
            
            # 将响应转换为Message对象
            if isinstance(response, dict):
                ai_message = Message(
                    role="assistant",
                    content=response.get("choices", [{}])[0].get("message", {}).get("content", "抱歉，处理失败")
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
        finally:
            self.set_loading_state(False)

    def clear_attachments(self):
        """清除所有附件"""
        self.attached_files.clear()
        # 清除预览区域的所有组件
        while self.preview_layout.count():
            item = self.preview_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        # 隐藏预览区域
        self.preview_scroll.setVisible(False)

    def update_display(self):
        """更新对话显示"""
        self.history_display.clear()
        for message in self.chat_history.get_messages():
            style = self.user_style if message.role == "user" else self.ai_style
            role_prefix = "用户: " if message.role == "user" else "AI: "
            content = f'<div style="{style}">{role_prefix}{message.content}</div>'
            
            if hasattr(message, 'attachments') and message.attachments:
                content += '<div style="margin-top: 5px;">附件:</div>'
                for attachment in message.attachments:
                    content += f'<div style="margin-left: 10px;">- {attachment["name"]}</div>'
            
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

    def init_message_styles(self):
        self.user_style = "background-color: #e3f2fd; padding: 5px; border-radius: 5px;"
        self.ai_style = "background-color: #f5f5f5; padding: 5px; border-radius: 5px;"

    def set_loading_state(self, is_loading: bool):
        self.send_button.setEnabled(not is_loading)
        self.send_button.setText("发送中..." if is_loading else "发送")
        self.status_bar.showMessage("正在处理..." if is_loading else "就绪")

    def setup_shortcuts(self):
        send_shortcut = QShortcut(QKeySequence("Return"), self)
        send_shortcut.activated.connect(self.send_message)
        
        clear_shortcut = QShortcut(QKeySequence("Ctrl+L"), self)
        clear_shortcut.activated.connect(self.clear_attachments)


class MessageCache:
    def __init__(self, max_size=100):
        self.messages = []
        self.max_size = max_size
        
    def add(self, message):
        self.messages.append(message)
        if len(self.messages) > self.max_size:
            self.messages.pop(0)
            
    def get_all(self):
        return self.messages

# 1. 添加文件大小限制
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# 2. 优化文件处理
def process_file(self, file_path: str) -> dict:
    file_size = os.path.getsize(file_path)
    if file_size > self.MAX_FILE_SIZE:
        raise ValueError(f"文件大小超过限制: {file_size / 1024 / 1024:.2f}MB")
        
    if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
        return self.process_image_file(file_path)
    else:
        return self.process_text_file(file_path)
