from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QTextEdit
from PyQt6.QtCore import Qt

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
        name_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                color: #2c3e50;
                padding: 8px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                margin-bottom: 8px;
            }
        """)
        layout.addWidget(name_label)
        
        # 分析结果显示区域
        self.result_display = QTextEdit()
        self.result_display.setReadOnly(True)
        self.result_display.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 12px;
                font-family: "Consolas", monospace;
                font-size: 10pt;
                line-height: 1.6;
            }
            QTextEdit:focus {
                border-color: #80bdff;
                outline: 0;
            }
        """)
        layout.addWidget(self.result_display)
        
        self.setLayout(layout)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin: 8px;
                padding: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
        """) 