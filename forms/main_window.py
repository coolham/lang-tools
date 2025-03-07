from PyQt6.QtWidgets import QMainWindow, QMenuBar, QStatusBar, QTabWidget
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from forms.markdown_form import MarkdownForm
from forms.artical_form import ArticleForm
from forms.chat_form import ChatForm
from utils.logger import Logger


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.logger = Logger.create_logger('main')
        self.init_ui()

    def init_ui(self):
        """初始化主窗口的UI"""
        self.setWindowTitle('Lang Tools')
        self.setGeometry(100, 100, 800, 600)

        # 初始化各个UI组件
        self.init_menu_bar()
        self.init_status_bar()
        self.init_tab_widget()

        self.show()

    def init_menu_bar(self):
        """初始化菜单栏"""
        menu_bar = self.menuBar()

        # 文件菜单
        file_menu = menu_bar.addMenu('File')
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 帮助菜单
        help_menu = menu_bar.addMenu('Help')
        about_action = QAction('About', self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def init_status_bar(self):
        """初始化状态栏"""
        self.statusBar().showMessage('Ready')

    def init_tab_widget(self):
        """初始化标签页"""
        tabs = QTabWidget()
        
        # Markdown标签页
        markdown_tab = MarkdownForm()
        tabs.addTab(markdown_tab, "Markdown")

        # Chat标签页
        chat_tab = ChatForm()
        tabs.addTab(chat_tab, "Chat")

        # Article标签页
        article_tab = ArticleForm()
        tabs.addTab(article_tab, "Article")

        self.setCentralWidget(tabs)

    def show_about_dialog(self):
        """显示关于对话框"""
        self.statusBar().showMessage('About Lang Tools')
