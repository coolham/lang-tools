from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                            QLineEdit, QPushButton, QLabel, QStatusBar,
                            QFileDialog, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QImage
from utils.logger import Logger
from services.models import Message, ChatHistory
from services.openai_service import OpenAIService
import os
import base64
from PIL import Image
import io


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


class ChatForm(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = Logger.create_logger('chat')
        self.chat_history = ChatHistory()
        self.ai_service = OpenAIService()  # 使用OpenAI SDK实现
        self.attached_files = []  # 存储已上传的文件路径
        self.init_ui()

    def init_ui(self):
        """初始化UI布局"""
        self.setWindowTitle('AI对话')
        layout = QVBoxLayout()

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
            ai_message = self.ai_service.send_message(self.chat_history.get_messages())
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
        
