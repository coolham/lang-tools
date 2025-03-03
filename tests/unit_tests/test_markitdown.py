import unittest
from converters.markdown_converter import MarkdownConverter
from common.config_manager import get_global_config

class TestMarkdownConverter(unittest.TestCase):
    def setUp(self):
        config = get_global_config()
        self.openai_api_url = config.get('openai.api_url')
        self.openai_api_key = config.get('openai.api_key')
        self.converter = MarkdownConverter(self.openai_api_url, self.openai_api_key)

    def test_convert_to_markdown_pdf(self):
        # 假设有一个测试用的PDF文件路径
        test_pdf_path = 'data/test1.pdf'
        result = self.converter.convert_to_markdown(test_pdf_path)
        self.assertIsInstance(result, str)
        # self.assertIn('#', result)  # 假设转换结果包含Markdown格式的标题

    def test_convert_to_markdown_word(self):
        # 假设有一个测试用的Word文件路径
        test_word_path = 'data/test1.docx'
        result = self.converter.convert_to_markdown(test_word_path)
        self.assertIsInstance(result, str)
        # self.assertIn('#', result)  # 假设转换结果包含Markdown格式的标题

    @unittest.skip("skipping docintel test")
    def test_convert_with_docintel(self):
        # 假设有一个测试用的PDF文件路径和文档智能端点
        test_pdf_path = 'data/test1.pdf'
        endpoint = 'http://example.com/docintel'
        result = self.converter.convert_with_docintel(test_pdf_path, endpoint)
        self.assertIsInstance(result, str)
        # self.assertIn('#', result)  # 假设转换结果包含Markdown格式的标题

    def test_convert_with_llm(self):
        # LLM模型只支持图片
        test_pdf_path = 'data/test_pic_01.png'
        llm_model = 'gpt-4o'
        result = self.converter.convert_with_llm(test_pdf_path, llm_model)
        self.assertIsInstance(result, str)
        self.assertIn('#', result)  # 假设转换结果包含Markdown格式的标题

if __name__ == '__main__':
    unittest.main()
