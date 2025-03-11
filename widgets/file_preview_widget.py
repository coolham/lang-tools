from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QFont, QColor
import os

class FilePreviewWidget(QFrame):
    """文件预览组件"""
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 文件名标签
        file_name = os.path.basename(self.file_path)
        name_label = QLabel(file_name)
        name_label.setWordWrap(True)
        name_label.setFont(QFont("Microsoft YaHei", 9))
        name_label.setStyleSheet("color: #333333;")
        layout.addWidget(name_label)
        
        # 预览区域
        preview_label = QLabel()
        preview_label.setFixedSize(120, 120)
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                border-radius: 8px;
            }
        """)
        
        # 根据文件类型显示不同的预览
        if self.file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            pixmap = QPixmap(self.file_path)
            scaled_pixmap = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio)
            preview_label.setPixmap(scaled_pixmap)
        else:
            preview_label.setText("📄")
            preview_label.setFont(QFont("Microsoft YaHei", 24))
            
        layout.addWidget(preview_label)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setFixedWidth(80)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff4d4f;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #ff7875;
            }
        """)
        delete_btn.clicked.connect(self.deleteLater)
        layout.addWidget(delete_btn)
        
        self.setLayout(layout)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
                border: 1px solid #e8e8e8;
            }
            QFrame:hover {
                border: 1px solid #1890ff;
            }
        """)
        self.setFixedSize(140, 200) 