from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QFileDialog, QSplitter
from PyQt6.QtCore import Qt
from converters.markdown_converter import MarkdownConverter
from utils.logger import Logger


class MarkdownForm(QWidget):
    def __init__(self):
        super().__init__()
        self.logger = Logger.create_logger('markdown')
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Markdown Form')

        # Main layout
        main_layout = QVBoxLayout()

        # Initialize UI components
        top_layout = self.init_top_layout()
        bottom_layout = self.init_bottom_layout()

        # Add layouts to main layout
        main_layout.addLayout(top_layout)
        main_layout.addWidget(bottom_layout)

        self.setLayout(main_layout)

    def init_top_layout(self):
        top_layout = QHBoxLayout()
        self.file_label = QLabel('No file selected')
        select_file_button = QPushButton('Select File')
        convert_button = QPushButton('Convert to Markdown')

        select_file_button.clicked.connect(self.select_file)
        convert_button.clicked.connect(self.convert_file)

        top_layout.addWidget(self.file_label)
        top_layout.addWidget(select_file_button)
        top_layout.addWidget(convert_button)

        return top_layout

    def init_bottom_layout(self):
        # Use QSplitter to allow resizing
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.markdown_editor = QTextEdit()
        self.markdown_preview = QTextEdit()
        self.markdown_preview.setReadOnly(True)

        splitter.addWidget(self.markdown_editor)
        splitter.addWidget(self.markdown_preview)

        return splitter

    def select_file(self):
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(self, 'Select File', '', 'Documents (*.pdf *.doc *.docx)')
        if file_path:
            self.file_label.setText(file_path)

    def convert_file(self):
        # Placeholder for file conversion logic
        self.markdown_editor.setPlainText('# Converted Markdown Content')
        self.markdown_preview.setPlainText('# Converted Markdown Content')