import os
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt
from typing import List, Dict, Any, Optional


class FileSelectionDialog(QDialog):
    """可重用的文件选择对话框
    
    用于从指定目录显示并选择多个文件，支持文件状态显示和排序。
    """
    
    def __init__(
        self, 
        parent=None, 
        directory: str = None, 
        file_index: Dict[str, Any] = None,
        selected_files: List[str] = None,
        title: str = "选择文件"
    ):
        """初始化文件选择对话框
        
        Args:
            parent: 父窗口
            directory: 文件目录路径
            file_index: 文件索引数据，结构为 {"files": {filename: {"index": int, "analysis_count": int, ...}}}
            selected_files: 当前已选择的文件路径列表
            title: 对话框标题
        """
        super().__init__(parent)
        
        self.directory = directory
        self.file_index = file_index or {"files": {}}
        self.selected_files = selected_files or []
        
        # 设置对话框属性
        self.setWindowTitle(title)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        # 应用样式
        self._apply_styles()
        
        # 创建UI
        self._init_ui()
    
    def _apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QListWidget {
                border: 1px solid #dee2e6;
                border-radius: 4px;
                background-color: #ffffff;
                padding: 5px;
                font-family: "Consolas", monospace;
                font-size: 10pt;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f8f9fa;
                margin: 2px;
                border-radius: 4px;
            }
            /* 设置交替行的基本样式 */
            QListWidget::item:alternate {
                background-color: #f8f9fa;
            }
            /* 确保选中状态覆盖交替行样式 */
            QListWidget::item:selected,
            QListWidget::item:alternate:selected {
                background-color: #007bff !important;
                color: white !important;
                font-weight: bold;
                border: 1px solid #0056b3;
            }
            /* 悬停样式 */
            QListWidget::item:hover:!selected,
            QListWidget::item:alternate:hover:!selected {
                background-color: #e9ecef;
                color: #212529;
            }
            /* 选中并悬停的样式 */
            QListWidget::item:selected:hover,
            QListWidget::item:alternate:selected:hover {
                background-color: #0056b3 !important;
                color: white !important;
            }
            /* 非活动窗口中的选中样式 */
            QListWidget::item:selected:!active,
            QListWidget::item:alternate:selected:!active {
                background-color: #6c757d;
                color: white;
            }
        """)
        
        # 按钮样式
        self.button_style = """
            QPushButton {
                background-color: %s;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: %s;
            }
            QPushButton:pressed {
                background-color: %s;
            }
        """
    
    def _init_ui(self):
        """初始化UI"""
        # 创建主布局
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 添加说明标签
        if self.directory:
            info_label = QLabel(f"当前目录: {self.directory}")
            info_label.setStyleSheet("""
                QLabel {
                    color: #495057;
                    font-weight: bold;
                    padding: 5px;
                    background-color: #f8f9fa;
                    border-radius: 4px;
                }
            """)
            info_label.setWordWrap(True)
            layout.addWidget(info_label)

        # 添加使用说明 - 说明如何使用多选功能
        usage_label = QLabel("多选提示: 使用Shift键可以选择连续的文件，使用Ctrl键可以选择非连续文件")
        usage_label.setStyleSheet("""
            QLabel {
                color: #6c757d;
                padding: 5px;
                font-style: italic;
            }
        """)
        usage_label.setWordWrap(True)
        layout.addWidget(usage_label)

        # 创建文件列表
        self.list_widget = QListWidget()
        # 改用ExtendedSelection模式，支持Shift多选和Ctrl多选
        self.list_widget.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.list_widget.setAlternatingRowColors(True)
        
        # 添加文件到列表
        self._populate_file_list()
        
        layout.addWidget(self.list_widget)

        # 添加选择计数标签
        self.selection_count_label = QLabel("已选择: 0 个文件")
        self.selection_count_label.setStyleSheet("""
            QLabel {
                color: #495057;
                padding: 5px;
            }
        """)
        layout.addWidget(self.selection_count_label)
        
        # 连接选择变化信号
        self.list_widget.itemSelectionChanged.connect(self._update_selection_count)
        
        # 添加按钮
        button_layout = QHBoxLayout()
        
        # 创建按钮
        select_all_btn = QPushButton("全选")
        select_all_btn.setStyleSheet(self.button_style % ('#6c757d', '#5a6268', '#545b62'))
        
        clear_btn = QPushButton("清除选择")
        clear_btn.setStyleSheet(self.button_style % ('#6c757d', '#5a6268', '#545b62'))
        
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet(self.button_style % ('#28a745', '#218838', '#1e7e34'))
        
        cancel_btn = QPushButton("取消")
        cancel_btn.setStyleSheet(self.button_style % ('#dc3545', '#c82333', '#bd2130'))

        # 添加按钮到布局
        button_layout.addWidget(select_all_btn)
        button_layout.addWidget(clear_btn)
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        # 绑定按钮事件
        select_all_btn.clicked.connect(self.list_widget.selectAll)
        clear_btn.clicked.connect(self.list_widget.clearSelection)
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        
        # 设置初始焦点到列表控件，以便键盘操作
        self.list_widget.setFocus()
        
        # 初始更新选择计数
        self._update_selection_count()
    
    def _populate_file_list(self):
        """填充文件列表"""
        if not self.directory or not self.file_index:
            return
        
        # 按索引排序文件
        sorted_files = sorted(
            self.file_index["files"].items(), 
            key=lambda x: x[1]["index"]
        )
        
        # 添加文件到列表
        for filename, info in sorted_files:
            # 创建带序号的显示文本
            display_text = f"{info['index']:04d}. {filename}"
            
            # 添加额外信息（如分析次数）
            if "last_analyzed" in info and info["last_analyzed"]:
                display_text += f" (已分析: {info.get('analysis_count', 0)}次)"
            
            item = QListWidgetItem(display_text)
            # 存储完整文件路径作为item的数据
            full_path = os.path.join(self.directory, filename)
            item.setData(Qt.ItemDataRole.UserRole, full_path)
            self.list_widget.addItem(item)
            
            # 如果文件已经被选中，设置为选中状态
            if full_path in self.selected_files:
                item.setSelected(True)
    
    def _update_selection_count(self):
        """更新选择计数"""
        count = len(self.list_widget.selectedItems())
        self.selection_count_label.setText(f"已选择: {count} 个文件")
    
    def get_selected_files(self) -> List[str]:
        """获取选中的文件路径列表
        
        Returns:
            List[str]: 选中的文件完整路径列表
        """
        return [
            item.data(Qt.ItemDataRole.UserRole)
            for item in self.list_widget.selectedItems()
        ]