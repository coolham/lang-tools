# from markitdown import MarkItDown
# from openai import OpenAI
from utils.logger import Logger
from utils.config_manager import ConfigManager


class MarkdownConverter:
    def __init__(self, openai_api_url: str = None, openai_api_key: str = None):
        # 初始化转换器
        self.logger = Logger.create_logger('markdown')
        self.md_docintel = None
        self.md_llm = None

        # 设置OpenAI API的URL和Key
        if openai_api_url and openai_api_key:
            # self.llm_client = OpenAI(base_url=openai_api_url, api_key=openai_api_key)
            pass
        else:
            self.llm_client = None

        # 获取全局配置
        config_manager = ConfigManager()
        self.config = config_manager.get_config()

    def convert_to_markdown(self, file_path: str) -> str:
        """
        将指定的文件转换为Markdown格式。

        :param file_path: 要转换的文件路径
        :return: 转换后的Markdown内容
        """
        self.logger.info(f"Converting file to markdown: {file_path}")
        self.md_basic = MarkItDown()
        # 检查文件类型并调用相应的转换方法
        if file_path.endswith('.pdf'):
            return self._convert_pdf_to_markdown(file_path)
        elif file_path.endswith('.doc') or file_path.endswith('.docx'):
            return self._convert_word_to_markdown(file_path)
        else:
            raise ValueError("Unsupported file type")

    def _convert_pdf_to_markdown(self, file_path: str) -> str:
        # 使用基本转换
        self.logger.info(f"Converting pdf to markdown: {file_path}")
        result = self.md_basic.convert(file_path)
        return result.text_content

    def _convert_word_to_markdown(self, file_path: str) -> str:
        # 使用基本转换
        self.logger.info(f"Converting word to markdown: {file_path}")
        result = self.md_basic.convert(file_path)
        return result.text_content

    def convert_with_docintel(self, file_path: str, endpoint: str) -> str:
        """
        使用文档智能进行转换。

        :param file_path: 要转换的文件路径
        :param endpoint: 文档智能服务的端点
        :return: 转换后的Markdown内容
        """
        self.logger.info(f"Converting with docintel: {file_path}")
        self.md_docintel = MarkItDown(docintel_endpoint=endpoint)
        result = self.md_docintel.convert(file_path)
        return result.text_content

    def convert_with_llm(self, file_path: str, llm_model: str) -> str:
        """
        使用大型语言模型进行转换。

        :param file_path: 要转换的文件路径，只支持图片
        :param llm_model: 使用的LLM模型名称
        :return: 转换后的Markdown内容
        """
        self.logger.info(f"Converting with llm: {file_path}")
        if not self.llm_client:
            raise ValueError("LLM client is not configured. Please provide OpenAI API URL and Key.")
        self.md_llm = MarkItDown(llm_client=self.llm_client, llm_model=llm_model)
        result = self.md_llm.convert(file_path)
        return result.text_content