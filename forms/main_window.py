from PyQt6.QtWidgets import QMainWindow, QMenuBar, QStatusBar, QTabWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from forms.markdown_form import MarkdownForm




class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Lang Tools')
        self.setGeometry(100, 100, 800, 600)

        # Create menu bar
        menu_bar = self.menuBar()

        # Add file menu
        file_menu = menu_bar.addMenu('File')
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Add help menu
        help_menu = menu_bar.addMenu('Help')
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        # Create status bar
        self.statusBar().showMessage('Ready')

        # Create tab widget
        tabs = QTabWidget()
        markdown_tab = MarkdownForm()
        tabs.addTab(markdown_tab, "Markdown")

        self.setCentralWidget(tabs)

        self.show()

    def show_about_dialog(self):
        self.statusBar().showMessage('About Lang Tools')
