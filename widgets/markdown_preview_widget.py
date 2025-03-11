from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
import markdown as md
from markdown.extensions.tables import TableExtension
from markdown.extensions.fenced_code import FencedCodeExtension
from markdown.extensions.toc import TocExtension
from utils.logger import Logger


class MarkdownPreviewWidget(QTextEdit):
    """
    一个专门用于预览Markdown内容的widget。
    提供Markdown到HTML的转换和美化显示功能。
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger.create_logger('markdown_preview')
        self.setReadOnly(True)
        self.setFont(QFont("Arial", 10))
        
        # 定义CSS样式
        self.css = """
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                padding: 20px;
                max-width: 800px;
                margin: 0 auto;
            }
            h1, h2, h3, h4, h5, h6 {
                margin-top: 24px;
                margin-bottom: 16px;
                font-weight: 600;
                line-height: 1.25;
            }
            h1 { font-size: 2em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }
            h2 { font-size: 1.5em; border-bottom: 1px solid #eaecef; padding-bottom: .3em; }
            h3 { font-size: 1.25em; }
            h4 { font-size: 1em; }
            p { margin-top: 0; margin-bottom: 16px; }
            code {
                font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
                padding: 0.2em 0.4em;
                margin: 0;
                font-size: 85%;
                background-color: rgba(27,31,35,0.05);
                border-radius: 3px;
            }
            pre {
                font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
                padding: 16px;
                overflow: auto;
                font-size: 85%;
                line-height: 1.45;
                background-color: #f6f8fa;
                border-radius: 3px;
            }
            pre code {
                padding: 0;
                background-color: transparent;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin-bottom: 16px;
            }
            table th, table td {
                padding: 6px 13px;
                border: 1px solid #dfe2e5;
            }
            table tr {
                background-color: #fff;
                border-top: 1px solid #c6cbd1;
            }
            table tr:nth-child(2n) {
                background-color: #f6f8fa;
            }
            img {
                max-width: 100%;
                box-sizing: border-box;
            }
            blockquote {
                padding: 0 1em;
                color: #6a737d;
                border-left: 0.25em solid #dfe2e5;
                margin-left: 0;
                margin-right: 0;
            }
        </style>
        """
        
        # 定义Markdown扩展
        self.extensions = [
            TableExtension(),
            FencedCodeExtension(),
            TocExtension(baselevel=1),
            'extra',  # 包含很多常用扩展
            'nl2br',  # 将换行转换为<br>标签
            'sane_lists',  # 更好的列表解析
        ]
    
    def update_preview(self, markdown_text):
        """
        更新预览内容。
        
        :param markdown_text: Markdown格式的文本
        """
        try:
            # 转换Markdown为HTML
            html_content = md.markdown(markdown_text, extensions=self.extensions)
            
            # 添加完整的HTML结构
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                {self.css}
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            
            self.setHtml(full_html)
            self.logger.debug("Preview updated successfully")
        except Exception as e:
            self.logger.error(f"Error updating preview: {str(e)}")
            # 降级到基本文本显示
            self.setPlainText(markdown_text) 