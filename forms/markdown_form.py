from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QFileDialog, \
    QSplitter, QProgressBar, QMessageBox, QGroupBox, QSizePolicy
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPageLayout, QPageSize, QPdfWriter
from PyQt6.QtPrintSupport import QPrinter
from converters.markdown_converter import MarkdownConverter
from utils.logger import Logger
from widgets.markdown_preview_widget import MarkdownPreviewWidget
import os


class ConversionThread(QThread):
    """
    A QThread class to handle the conversion process in a separate thread.
    This allows the GUI to remain responsive while the conversion is in progress.
    """
    conversion_started = pyqtSignal()
    conversion_finished = pyqtSignal(str)  # Pass the converted text as a string
    conversion_error = pyqtSignal(str)

    def __init__(self, file_path, converter):
        super().__init__()
        self.file_path = file_path
        self.converter = converter
        self.markdown_text = None

    def run(self):
        self.conversion_started.emit()
        try:
            self.markdown_text = self.converter.convert_to_markdown(self.file_path)
            self.conversion_finished.emit(self.markdown_text)  # Emit the signal with the converted text
        except Exception as e:
            self.conversion_error.emit(str(e))


class MarkdownForm(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = Logger.create_logger('markdown')
        self.converter = MarkdownConverter()  # Initialize the converter
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Markdown Form')

        # Main layout
        main_layout = QVBoxLayout()

        # Initialize UI components and add to main layout
        convert_layout = self.init_convert_layout()
        display_layout = self.init_display_layout()
        
        main_layout.addWidget(convert_layout)
        main_layout.addWidget(display_layout)

        self.setLayout(main_layout)

    def init_convert_layout(self):
        group_box = QGroupBox('文件转换')
        group_layout = QHBoxLayout()  # 改为水平布局，让所有控件在一行
        group_box.setLayout(group_layout)
        
        # 文件选择部分
        file_layout = QHBoxLayout()
        self.file_label = QLabel('No file selected')
        self.file_label.setMinimumWidth(150)
        self.file_label.setMaximumWidth(300)
        select_file_button = QPushButton('选择文件')
        select_file_button.setMaximumWidth(100)
        select_file_button.clicked.connect(self.select_file)
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(select_file_button)
        
        # 按钮部分
        convert_button = QPushButton('转换')
        convert_button.setMaximumWidth(80)
        save_md_button = QPushButton('保存MD')
        save_md_button.setMaximumWidth(80)
        save_pdf_button = QPushButton('保存PDF')
        save_pdf_button.setMaximumWidth(80)
        
        convert_button.clicked.connect(self.convert_file)
        save_md_button.clicked.connect(self.save_as_markdown)
        save_pdf_button.clicked.connect(self.save_as_pdf)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(15)
        
        # 将所有控件添加到同一行
        group_layout.addLayout(file_layout, 4)  # 文件选择部分占据更多空间
        group_layout.addWidget(convert_button, 1)
        group_layout.addWidget(save_md_button, 1)
        group_layout.addWidget(save_pdf_button, 1)
        group_layout.addWidget(self.progress_bar, 2)
        
        # 设置GroupBox的大小策略，使其不会占用过多垂直空间
        group_box.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        group_box.setMaximumHeight(80)
        
        return group_box

    def init_display_layout(self):
        # Use QSplitter to allow resizing
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Markdown editor
        self.markdown_editor = QTextEdit()
        self.markdown_editor.setFont(QFont("Courier New", 10))
        self.markdown_editor.textChanged.connect(self.update_preview)
        
        # Markdown preview using the new widget
        self.markdown_preview = MarkdownPreviewWidget()

        splitter.addWidget(self.markdown_editor)
        splitter.addWidget(self.markdown_preview)
        
        # Set initial sizes for the splitter
        splitter.setSizes([400, 400])

        return splitter

    def select_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, 'Select File', '', 'Documents (*.pdf *.doc *.docx)')
        if file_path:
            self.file_label.setText(file_path)
            self.logger.info(f"File selected: {file_path}")

    def convert_file(self):
        file_path = self.file_label.text()
        if file_path == 'No file selected':
            self.logger.warning("No file selected for conversion")
            return
            
        self.logger.info(f"Starting conversion of file: {file_path}")
        
        # Create and start the conversion thread
        self.conversion_thread = ConversionThread(file_path, self.converter)
        
        # Connect signals to slots
        self.conversion_thread.conversion_started.connect(self.on_conversion_started)
        self.conversion_thread.conversion_finished.connect(self.on_conversion_finished)
        self.conversion_thread.conversion_error.connect(self.on_conversion_error)
        
        # Start the thread
        self.conversion_thread.start()

    def update_preview(self):
        # Use the new widget's method
        self.markdown_preview.update_preview(self.markdown_editor.toPlainText())

    def on_conversion_started(self):
        # This slot is called when the conversion starts
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.logger.info("Conversion started")

    def on_conversion_finished(self, markdown_text):
        # This slot is called when the conversion is finished
        self.progress_bar.setVisible(False)
        self.markdown_editor.setPlainText(markdown_text)
        
        # Update the preview
        self.update_preview()
        
        self.logger.info("Conversion finished successfully")

    def on_conversion_error(self, error_message):
        # This slot is called when an error occurs during conversion
        self.progress_bar.setVisible(False)
        self.markdown_editor.setPlainText(f"Error during conversion: {error_message}")
        self.logger.error(f"Conversion error: {error_message}")

    def save_as_markdown(self):
        """保存当前内容为Markdown文件"""
        if not self.markdown_editor.toPlainText():
            QMessageBox.warning(self, "保存失败", "没有内容可保存")
            return
            
        # 获取要保存的文件路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存Markdown文件", "", "Markdown Files (*.md);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.markdown_editor.toPlainText())
                self.logger.info(f"Markdown文件已保存到: {file_path}")
                QMessageBox.information(self, "保存成功", f"文件已保存到: {file_path}")
            except Exception as e:
                self.logger.error(f"保存Markdown文件时出错: {str(e)}")
                QMessageBox.critical(self, "保存失败", f"保存文件时出错: {str(e)}")

    def save_as_pdf(self):
        """保存当前内容为PDF文件"""
        if not self.markdown_editor.toPlainText():
            QMessageBox.warning(self, "保存失败", "没有内容可保存")
            return
            
        # 获取要保存的文件路径
        file_path, _ = QFileDialog.getSaveFileName(
            self, "保存PDF文件", "", "PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            try:
                # 使用QPrinter保存为PDF
                printer = QPrinter(QPrinter.PrinterMode.HighResolution)
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(file_path)
                
                # 设置页面布局
                layout = QPageLayout()
                layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                layout.setOrientation(QPageLayout.Orientation.Portrait)
                printer.setPageLayout(layout)
                
                # 使用预览组件渲染HTML并打印到PDF
                self.markdown_preview.document().print(printer)
                
                self.logger.info(f"PDF文件已保存到: {file_path}")
                QMessageBox.information(self, "保存成功", f"文件已保存到: {file_path}")
            except Exception as e:
                self.logger.error(f"保存PDF文件时出错: {str(e)}")
                QMessageBox.critical(self, "保存失败", f"保存文件时出错: {str(e)}")