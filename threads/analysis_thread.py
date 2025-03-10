from PyQt6.QtCore import QThread, pyqtSignal
from utils.logger import Logger
from services.message_types import Message
import os
import fitz  # PyMuPDF
from typing import List, Dict

"""
分析线程
"""
class AnalysisThread(QThread):
    """分析线程"""
    progress_updated = pyqtSignal(int)
    analysis_completed = pyqtSignal(str, str)  # 文件名, 分析结果
    error_occurred = pyqtSignal(str, str)  # 文件名, 错误信息
    status_updated = pyqtSignal(str)  # 状态更新信号

    # 每个chunk的最大token数（根据不同模型调整）
    MAX_CHUNK_TOKENS = 4000  # 预留一些空间给指令和响应
    # 每页估算的平均token数（英文约为字数的1.3倍）
    TOKENS_PER_PAGE = 500

    def __init__(self, file_path: str, ai_service, instruction: str):
        super().__init__()
        self.file_path = file_path
        self.ai_service = ai_service
        self.instruction = instruction
        self.logger = Logger.create_logger('analysis_thread')
        self.doc = None

    def estimate_tokens(self, text: str) -> int:
        """估算文本的token数量（粗略估算）"""
        # 英文单词数（按空格分割）
        words = len(text.split())
        # 中文字符数
        chinese = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        # 估算token数（英文单词约1.3倍，中文字符约2倍）
        return int(words * 1.3 + chinese * 2)

    def split_text_into_chunks(self, text: str) -> List[str]:
        """将文本分割成适合token限制的块"""
        chunks = []
        current_chunk = ""
        current_tokens = 0
        
        # 按段落分割文本
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            paragraph_tokens = self.estimate_tokens(paragraph)
            
            # 如果单个段落就超过限制，需要进一步分割
            if paragraph_tokens > self.MAX_CHUNK_TOKENS:
                # 按句子分割
                sentences = paragraph.split('. ')
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                        
                    sentence_tokens = self.estimate_tokens(sentence)
                    
                    if current_tokens + sentence_tokens <= self.MAX_CHUNK_TOKENS:
                        current_chunk += sentence + '. '
                        current_tokens += sentence_tokens
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + '. '
                        current_tokens = sentence_tokens
            else:
                # 检查是否需要开始新的chunk
                if current_tokens + paragraph_tokens > self.MAX_CHUNK_TOKENS:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph + '\n\n'
                    current_tokens = paragraph_tokens
                else:
                    current_chunk += paragraph + '\n\n'
                    current_tokens += paragraph_tokens
        
        # 添加最后一个chunk
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks

    def analyze_chunk(self, chunk: str, chunk_index: int, total_chunks: int) -> str:
        """分析单个文本块"""
        try:
            # 为每个块创建特定的指令
            chunk_instruction = f"""这是一篇论文的第 {chunk_index + 1}/{total_chunks} 部分。
请专注于以下两点：
1. 判断该论文的实现类型（official/unofficial）
2. 寻找支持你判断的具体证据

{self.instruction}

注意：
- 如果这不是第一部分，请基于前文继续分析
- 如果不是最后一部分，请等待后续内容再做最终判断
- 重点关注作者身份、机构归属、代码仓库信息等关键线索
"""
            # 创建消息
            messages = [
                Message(role="system", content="你是一个专业的论文分析助手，专注于判断论文实现的类型（official/unofficial）。请仔细寻找能够支持判断的证据。"),
                Message(role="user", content=f"{chunk_instruction}\n\n{chunk}")
            ]

            # 发送请求
            response = self.ai_service.send_message(messages)
            
            # 处理响应
            if isinstance(response, dict):
                content = response["choices"][0]["message"]["content"]
            else:
                content = response.choices[0].message.content
                
            return content
            
        except Exception as e:
            self.logger.error(f"分析文本块时发生错误: {str(e)}")
            raise

    def analyze_pdf(self, file_path: str) -> Dict:
        """分析PDF文件"""
        try:
            # 读取PDF内容
            pdf_text = self.read_pdf(file_path)
            
            # 分割文本
            text_chunks = self.split_text_into_chunks(pdf_text)
            
            # 分析每个文本块
            analysis_results = []
            for i, chunk in enumerate(text_chunks, 1):
                self.status_updated.emit(f"Analyzing chunk {i}/{len(text_chunks)} of {os.path.basename(file_path)}")
                
                # 构建消息
                messages = [
                    Message(role="system", content="你是一个专业的学术论文分析助手，专注于判断论文实现的类型（official/unofficial）。"),
                    Message(role="user", content=f"{self.instruction}\n\n{chunk}")
                ]
                
                # 发送到AI服务
                response = self.ai_service.send_message(messages)
                if response and hasattr(response, 'choices'):
                    analysis_results.append(response.choices[0].message.content)
            
            # 生成最终分析
            self.status_updated.emit(f"Generating final summary for {os.path.basename(file_path)}")
            final_analysis = self.generate_final_analysis(analysis_results)
            
            return {
                "file_path": file_path,
                "directory": os.path.dirname(file_path),
                "filename": os.path.basename(file_path),
                "content": final_analysis,
                "analysis_status": "已分析"
            }
            
        except Exception as e:
            self.logger.error(f"分析PDF文件时发生错误: {str(e)}")
            raise

    def run(self):
        try:
            # 清理文件名，移除._前缀
            base_name = os.path.basename(self.file_path)
            if base_name.startswith('._'):
                clean_path = os.path.join(os.path.dirname(self.file_path), base_name[2:])
                if os.path.exists(clean_path):
                    self.file_path = clean_path
                else:
                    raise FileNotFoundError(f"找不到原始文件: {clean_path}")

            self.status_updated.emit(f"Reading file: {os.path.basename(self.file_path)}")
            self.logger.info(f"Processing file: {self.file_path}")
            
            # 检查文件是否存在和可访问
            if not os.path.exists(self.file_path):
                raise FileNotFoundError(f"文件不存在: {self.file_path}")
                
            if not os.access(self.file_path, os.R_OK):
                raise PermissionError(f"无法读取文件: {self.file_path}")
            
            text_content = ""
            try:
                # 读取PDF文件
                self.doc = fitz.open(self.file_path)
                for page in self.doc:
                    text_content += page.get_text()
                self.logger.info(f"File reading completed: {self.file_path}")

                if not text_content.strip():
                    raise ValueError(f"文件内容为空: {self.file_path}")

                # 分割文本
                chunks = self.split_text_into_chunks(text_content)
                self.logger.info(f"文本已分割为 {len(chunks)} 个块")

                # 分析每个块
                analysis_results = []
                for i, chunk in enumerate(chunks):
                    self.status_updated.emit(f"Analyzing chunk {i + 1}/{len(chunks)} of {os.path.basename(self.file_path)}")
                    chunk_result = self.analyze_chunk(chunk, i, len(chunks))
                    analysis_results.append(chunk_result)

                # 如果有多个块，需要进行最终汇总
                if len(chunks) > 1:
                    self.status_updated.emit(f"Generating final summary for {os.path.basename(self.file_path)}")
                    summary_instruction = f"""这是对前面{len(chunks)}个部分分析的汇总。请生成一个完整的分析报告，格式如下：

1. 基本信息
- 标题：[从PDF文件名或内容中提取]
- 作者：[从论文中提取]

2. 实现情况分析
- 实现类型：[必须是official/unofficial/未知之一]
- 判断依据：[列出所有支持你判断的具体证据]
- 代码开源：[是/否]
- 代码链接：[如果有，提供链接]

注意：
1. 必须明确给出实现类型的判断
2. 判断依据必须具体，不能笼统
3. 如果无法判断类型，标注为"未知"并说明原因

各部分分析结果：
{''.join(f'第{i+1}部分分析：\n{result}\n\n' for i, result in enumerate(analysis_results))}
"""
                    # 创建汇总消息
                    summary_messages = [
                        Message(role="system", content="你是一个专业的论文分析助手，专注于判断论文实现的类型（official/unofficial）。请基于所有分析结果，给出最终的判断和完整的分析报告。"),
                        Message(role="user", content=summary_instruction)
                    ]

                    # 获取汇总结果
                    response = self.ai_service.send_message(summary_messages)
                    if isinstance(response, dict):
                        final_result = response["choices"][0]["message"]["content"]
                    else:
                        final_result = response.choices[0].message.content
                else:
                    # 如果只有一个块，直接使用其结果
                    final_result = analysis_results[0]

                self.logger.info(f"File analysis completed: {self.file_path}")
                self.analysis_completed.emit(os.path.basename(self.file_path), final_result)

            except fitz.FileDataError as e:
                raise ValueError(f"PDF文件格式错误: {str(e)}")
            finally:
                # 确保文件被关闭
                if self.doc:
                    self.doc.close()
                    self.doc = None

        except FileNotFoundError as e:
            self.logger.error(f"文件不存在: {str(e)}")
            self.error_occurred.emit(os.path.basename(self.file_path), str(e))
        except PermissionError as e:
            self.logger.error(f"文件访问权限错误: {str(e)}")
            self.error_occurred.emit(os.path.basename(self.file_path), str(e))
        except ValueError as e:
            self.logger.error(f"文件处理错误: {str(e)}")
            self.error_occurred.emit(os.path.basename(self.file_path), str(e))
        except Exception as e:
            self.logger.error(f"处理文件时发生错误: {self.file_path}, 错误: {str(e)}")
            self.error_occurred.emit(os.path.basename(self.file_path), str(e)) 