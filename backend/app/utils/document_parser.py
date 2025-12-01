"""
文档解析器
支持TXT和Markdown格式的文档解析和文本切分
"""
from typing import List, Dict, Any, Optional, Tuple
import re
import chardet


class DocumentParser:
    """文档解析器基类"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        Args:
            chunk_size: 文本块大小（字符数）
            chunk_overlap: 文本块重叠大小（字符数）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def parse(self, content: bytes) -> str:
        """
        解析文档内容
        
        Args:
            content: 文档内容（bytes）
        
        Returns:
            str: 解析后的文本
        """
        raise NotImplementedError
    
    def split_into_chunks(self, text: str, mode: str = 'fixed') -> List[Dict[str, Any]]:
        """
        将文本切分为文本块
        
        Args:
            text: 文本内容
            mode: 切分模式 ('fixed'|'paragraph'|'sentence'|'custom')
        
        Returns:
            List[Dict]: 文本块列表，每个块包含content、index、char_count等
        """
        if not text or not text.strip():
            return []
        
        if mode == 'paragraph':
            return self._split_by_paragraph(text)  # 单换行
        elif mode == 'paragraph_double':
            return self._split_by_paragraph_double(text)  # 双换行
        elif mode == 'sentence':
            return self._split_by_sentence(text)
        else:  # fixed 或 custom
            return self._split_by_fixed_size(text)
    
    def _split_by_fixed_size(self, text: str) -> List[Dict[str, Any]]:
        """
        按固定大小切分（简化安全版本）
        
        核心原则：
        1. 永远确保 start 向前移动
        2. 严格限制迭代次数
        3. 避免复杂的边界判断
        """
        import logging
        logger = logging.getLogger(__name__)
        
        chunks = []
        chunk_index = 0
        start = 0
        text_length = len(text)
        
        # 🚨 严格的迭代限制：最多文本长度的2倍，绝对不超过1000次
        max_iterations = min((text_length // max(1, self.chunk_size)) * 2 + 10, 1000)
        iteration = 0
        
        logger.info(f"开始按固定大小切分，文本长度: {text_length}, chunk_size: {self.chunk_size}, overlap: {self.chunk_overlap}, max_iter: {max_iterations}")
        
        while start < text_length and iteration < max_iterations:
            iteration += 1
            
            # 🚨 每10次迭代输出进度
            if iteration % 10 == 0:
                logger.info(f"切分进度: 迭代 {iteration}/{max_iterations}, start={start}/{text_length} ({start*100//text_length}%)")
            
            # 确定当前块的结束位置（简单直接）
            end = min(start + self.chunk_size, text_length)
            
            # 🚨 严格检查：end 必须大于 start
            if end <= start:
                logger.error(f"检测到异常：end({end}) <= start({start})，强制终止！")
                break
            
            # 提取文本块（不使用strip，保持原始长度）
            chunk_text = text[start:end]
            
            # 只过滤完全空白的块
            if chunk_text and chunk_text.strip():
                chunks.append({
                    'content': chunk_text.strip(),
                    'chunk_index': chunk_index,
                    'char_count': len(chunk_text.strip()),
                    'token_count': self.estimate_token_count(chunk_text),
                    'metadata': {
                        'start_position': start,
                        'end_position': end,
                        'split_mode': 'fixed'
                    }
                })
                chunk_index += 1
            
            # 🚨 安全的位置移动：确保至少前进 1 个字符
            # 优先使用 overlap，但如果 overlap 太大，至少前进 chunk_size 的 1/4
            min_step = max(1, self.chunk_size // 4)
            next_start = end - self.chunk_overlap
            
            if next_start <= start:
                # 强制至少前进 min_step
                next_start = start + min_step
                logger.warning(f"检测到位置未前进，强制前进 {min_step} 个字符 (start={start} -> {next_start})")
            
            # 🚨 最终检查：如果 next_start 仍然没有前进，直接跳到 end
            if next_start <= start:
                next_start = end
                logger.error(f"严重错误：位置仍未前进，强制跳到 end={end}")
            
            start = next_start
        
        # 🚨 检查是否因为迭代限制而终止
        if iteration >= max_iterations and start < text_length:
            logger.error(f"切分因迭代次数限制而终止！已迭代 {iteration} 次，start={start}, text_length={text_length}")
            logger.error(f"剩余文本长度: {text_length - start} 字符，已生成 {len(chunks)} 个块")
        else:
            logger.info(f"切分完成，共生成 {len(chunks)} 个文本块，迭代 {iteration} 次")
        
        return chunks
    
    def _split_by_paragraph(self, text: str) -> List[Dict[str, Any]]:
        """按段落切分（使用单换行符）- 每个换行分隔的内容就是一个独立的块"""
        # 按单换行符分割，每个换行分隔的内容就是一个独立的块
        lines = text.split('\n')
        chunks = []
        start_pos = 0
        
        for chunk_index, line in enumerate(lines):
            line = line.strip()
            # 跳过空行
            if not line:
                start_pos += 1  # 换行符占1个字符
                continue
            
            # 每个非空行就是一个独立的文本块
            chunks.append({
                'content': line,
                'chunk_index': chunk_index,
                'char_count': len(line),
                'token_count': self.estimate_token_count(line),
                'metadata': {
                    'start_position': start_pos,
                    'end_position': start_pos + len(line),
                    'split_mode': 'paragraph'
                }
            })
            start_pos += len(line) + 1  # 内容长度 + 换行符
        
        return chunks
    
    def _split_by_paragraph_double(self, text: str) -> List[Dict[str, Any]]:
        """按段落切分（使用双换行符）
        
        每个双换行符分隔的段落作为一个独立的chunk，不合并段落
        如果段落本身超过chunk_size，则按固定大小切分
        """
        # 按双换行符分割段落
        paragraphs = re.split(r'\n\n+', text)
        chunks = []
        chunk_index = 0
        start_pos = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                # 跳过空段落，但需要更新位置（双换行符占2个字符）
                # 注意：这里无法精确计算位置，因为不知道前面有多少个换行
                continue
            
            # 每个段落作为一个独立的chunk，不合并
            # 如果段落本身太长，按固定大小切分
            if len(para) > self.chunk_size:
                # 段落太长，需要进一步切分
                sub_chunks = self._split_long_paragraph(para, chunk_index, start_pos)
                chunks.extend(sub_chunks)
                chunk_index += len(sub_chunks)
                # 更新位置（近似值，因为无法精确计算双换行符的位置）
                start_pos += len(para) + 2
            else:
                # 段落大小合适，作为一个chunk
                chunks.append({
                    'content': para,
                    'chunk_index': chunk_index,
                    'char_count': len(para),
                    'token_count': self.estimate_token_count(para),
                    'metadata': {
                        'start_position': start_pos,
                        'end_position': start_pos + len(para),
                        'split_mode': 'paragraph_double'
                    }
                })
                chunk_index += 1
                # 更新位置（近似值）
                start_pos += len(para) + 2
        
        return chunks
    
    def _split_by_sentence(self, text: str) -> List[Dict[str, Any]]:
        """按句子切分"""
        # 按句号、问号、叹号分割句子
        sentences = re.split(r'([。？！；])', text)
        
        # 重新组合句子和标点
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                combined_sentences.append(sentences[i] + sentences[i + 1])
            else:
                combined_sentences.append(sentences[i])
        
        chunks = []
        chunk_index = 0
        current_chunk = ""
        start_pos = 0
        
        for sentence in combined_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # 如果当前块加上新句子不超过块大小，合并
            if len(current_chunk) + len(sentence) < self.chunk_size:
                current_chunk += sentence
            else:
                # 保存当前块
                if current_chunk:
                    chunks.append({
                        'content': current_chunk,
                        'chunk_index': chunk_index,
                        'char_count': len(current_chunk),
                        'token_count': self.estimate_token_count(current_chunk),
                        'metadata': {
                            'start_position': start_pos,
                            'end_position': start_pos + len(current_chunk),
                            'split_mode': 'sentence'
                        }
                    })
                    chunk_index += 1
                    start_pos += len(current_chunk)
                
                current_chunk = sentence
        
        # 保存最后一块
        if current_chunk:
            chunks.append({
                'content': current_chunk,
                'chunk_index': chunk_index,
                'char_count': len(current_chunk),
                'token_count': self.estimate_token_count(current_chunk),
                'metadata': {
                    'start_position': start_pos,
                    'end_position': start_pos + len(current_chunk),
                    'split_mode': 'sentence'
                }
            })
        
        return chunks
    
    def _split_long_paragraph(self, paragraph: str, start_index: int, start_pos: int) -> List[Dict[str, Any]]:
        """
        切分过长的段落（简化安全版本）
        
        🚨 关键修复：确保 start 始终向前移动，即使 chunk_text 为空
        """
        import logging
        logger = logging.getLogger(__name__)
        
        chunks = []
        start = 0
        para_len = len(paragraph)
        max_iterations = (para_len // max(1, self.chunk_size)) + 10
        iteration = 0
        
        while start < para_len and iteration < max_iterations:
            iteration += 1
            end = min(start + self.chunk_size, para_len)
            
            # 🚨 检查：end 必须大于 start
            if end <= start:
                logger.error(f"_split_long_paragraph: end({end}) <= start({start})，终止循环")
                break
            
            chunk_text = paragraph[start:end].strip()
            
            if chunk_text:
                chunks.append({
                    'content': chunk_text,
                    'chunk_index': start_index + len(chunks),
                    'char_count': len(chunk_text),
                    'token_count': self.estimate_token_count(chunk_text),
                    'metadata': {
                        'start_position': start_pos + start,
                        'end_position': start_pos + end,
                        'split_mode': 'paragraph_long'
                    }
                })
            
            # 🚨 关键修复：无论 chunk_text 是否为空，都要移动 start
                start = end
        
        if iteration >= max_iterations:
            logger.error(f"_split_long_paragraph: 达到最大迭代次数 {max_iterations}")
        
        return chunks
    
    @staticmethod
    def estimate_token_count(text: str) -> int:
        """
        估算token数量
        中文按1个字符=1个token，英文按4个字符=1个token估算
        优化版：避免使用正则表达式，直接遍历字符
        """
        if not text:
            return 0
        
        chinese_chars = 0
        # ✅ 直接遍历，比正则快很多
        for char in text:
            # 判断是否为中文字符（包括中日韩统一表意文字）
            if '\u4e00' <= char <= '\u9fff':
                chinese_chars += 1
        
        other_chars = len(text) - chinese_chars
        return chinese_chars + (other_chars // 4)
    
    @staticmethod
    def detect_encoding(content: bytes, return_confidence: bool = False) -> str:
        """
        检测文件编码
        
        Args:
            content: 文件内容（bytes）
            return_confidence: 是否返回置信度信息
        
        Returns:
            str: 检测到的编码名称（如'utf-8', 'gbk', 'gb2312'等）
            或 tuple: (编码名称, 置信度) if return_confidence=True
        """
        # 使用 chardet 检测编码
        detected = chardet.detect(content)
        encoding = detected.get('encoding', 'utf-8')
        confidence = detected.get('confidence', 0.0)
        
        # 如果置信度太低，尝试常见编码
        if confidence < 0.7:
            # 中文常见编码列表
            common_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'big5']
            
            for enc in common_encodings:
                try:
                    content.decode(enc)
                    encoding = enc
                    confidence = 0.99  # 手动设置高置信度
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
        
        # 编码名称标准化
        if encoding:
            encoding = encoding.lower()
            # GB2312 是 GBK 的子集，使用 GBK 更保险
            if encoding in ['gb2312', 'gb18030']:
                encoding = 'gbk'
        else:
            encoding = 'utf-8'
        
        if return_confidence:
            return encoding, confidence
        return encoding


class TxtParser(DocumentParser):
    """纯文本文档解析器"""
    
    def parse(self, content: bytes) -> str:
        """
        解析TXT文件，智能处理编码
        
        Args:
            content: 文件内容（bytes）
        
        Returns:
            str: 解析后的文本
        
        Raises:
            ValueError: 如果文件无法解码
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # 自动检测编码
        encoding, confidence = self.detect_encoding(content, return_confidence=True)
        logger.info(f"检测到文件编码: {encoding} (置信度: {confidence:.2%})")
        
        # 尝试使用检测到的编码
        text = None
        try:
            text = content.decode(encoding)
            logger.info(f"成功使用 {encoding} 编码解析文件")
        except (UnicodeDecodeError, LookupError) as e:
            logger.warning(f"使用 {encoding} 解码失败: {str(e)}")
            
            # 尝试常见编码
            fallback_encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1', 'cp1252']
            for fallback_enc in fallback_encodings:
                if fallback_enc == encoding:
                    continue  # 跳过已经尝试过的
                try:
                    text = content.decode(fallback_enc)
                    logger.info(f"回退使用 {fallback_enc} 编码成功")
                    break
                except (UnicodeDecodeError, LookupError):
                    continue
            
            # 如果所有编码都失败，使用 UTF-8 并忽略错误
            if text is None:
                logger.warning("所有编码尝试失败，使用 UTF-8 并忽略错误字符")
                text = content.decode('utf-8', errors='replace')
                # 替换掉乱码字符
                text = text.replace('�', '')
        
        # 检查是否有过多的乱码字符（可能编码错误）
        if text:
            invalid_ratio = text.count('�') / len(text) if len(text) > 0 else 0
            if invalid_ratio > 0.1:  # 超过10%是乱码
                logger.error(f"文件包含过多乱码字符 ({invalid_ratio:.1%})，可能编码识别错误")
                raise ValueError(f"文件编码错误，包含 {invalid_ratio:.1%} 的乱码字符。请确保文件使用 UTF-8、GBK 或 GB2312 编码")
        
        # 规范化换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 去除多余的空行（保留一个）
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 去除 BOM 标记
        if text.startswith('\ufeff'):
            text = text[1:]
        
        return text.strip()


class MarkdownParser(DocumentParser):
    """Markdown文档解析器"""
    
    def parse(self, content: bytes) -> str:
        """
        解析Markdown文件，智能处理编码
        
        Args:
            content: 文件内容（bytes）
        
        Returns:
            str: 解析后的文本
        
        Raises:
            ValueError: 如果文件无法解码
        """
        import logging
        logger = logging.getLogger(__name__)
        
        text = None
        
        # Markdown通常是UTF-8编码，优先尝试
        try:
            text = content.decode('utf-8')
            logger.info("成功使用 UTF-8 编码解析 Markdown 文件")
        except UnicodeDecodeError:
            logger.warning("UTF-8 解码失败，尝试自动检测编码")
            
            # 回退到自动检测
            encoding, confidence = self.detect_encoding(content, return_confidence=True)
            logger.info(f"检测到文件编码: {encoding} (置信度: {confidence:.2%})")
            
            try:
                text = content.decode(encoding)
                logger.info(f"成功使用 {encoding} 编码解析文件")
            except (UnicodeDecodeError, LookupError):
                logger.warning(f"使用 {encoding} 解码失败，尝试其他编码")
                
                # 尝试其他常见编码
                fallback_encodings = ['gbk', 'gb2312', 'gb18030', 'latin-1']
                for fallback_enc in fallback_encodings:
                    if fallback_enc == encoding:
                        continue
                    try:
                        text = content.decode(fallback_enc)
                        logger.info(f"回退使用 {fallback_enc} 编码成功")
                        break
                    except (UnicodeDecodeError, LookupError):
                        continue
                
                # 最后的回退：UTF-8 with replace
                if text is None:
                    logger.warning("所有编码尝试失败，使用 UTF-8 并替换错误字符")
                    text = content.decode('utf-8', errors='replace')
                    text = text.replace('�', '')
        
        # 检查乱码比例
        if text:
            invalid_ratio = text.count('�') / len(text) if len(text) > 0 else 0
            if invalid_ratio > 0.1:
                logger.error(f"Markdown 文件包含过多乱码字符 ({invalid_ratio:.1%})")
                raise ValueError(f"文件编码错误，包含 {invalid_ratio:.1%} 的乱码字符。建议使用 UTF-8 编码保存 Markdown 文件")
        
        # 规范化换行符
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # 去除 BOM 标记
        if text.startswith('\ufeff'):
            text = text[1:]
        
        return text.strip()
    
    def split_into_chunks(self, text: str) -> List[Dict[str, Any]]:
        """
        Markdown智能切分
        优先按标题层级切分，其次按段落
        """
        if not text or not text.strip():
            return []
        
        # 尝试按标题切分
        chunks = self._split_by_headers(text)
        
        # 如果没有标题或者块太大，使用默认切分
        if not chunks or any(len(c['content']) > self.chunk_size * 2 for c in chunks):
            return super().split_into_chunks(text)
        
        return chunks
    
    def _split_by_headers(self, text: str) -> List[Dict[str, Any]]:
        """按Markdown标题切分"""
        # 匹配Markdown标题（# ## ### 等）
        header_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
        
        chunks = []
        chunk_index = 0
        last_pos = 0
        
        # 提取所有标题位置
        headers = [(m.start(), m.end(), m.group(1), m.group(2)) 
                   for m in header_pattern.finditer(text)]
        
        if not headers:
            return []
        
        # 按标题切分
        for i, (start, end, level, title) in enumerate(headers):
            # 获取到下一个标题之前的内容
            if i < len(headers) - 1:
                next_start = headers[i + 1][0]
                chunk_text = text[start:next_start].strip()
            else:
                chunk_text = text[start:].strip()
            
            if chunk_text:
                chunks.append({
                    'content': chunk_text,
                    'chunk_index': chunk_index,
                    'char_count': len(chunk_text),
                    'token_count': self.estimate_token_count(chunk_text),
                    'metadata': {
                        'header_level': len(level),
                        'header_title': title,
                        'start_position': start,
                        'end_position': start + len(chunk_text)
                    }
                })
                chunk_index += 1
        
        return chunks


def get_parser(file_type: str, chunk_size: int = 500, chunk_overlap: int = 50) -> DocumentParser:
    """
    获取文档解析器
    
    Args:
        file_type: 文件类型（txt/md）
        chunk_size: 文本块大小
        chunk_overlap: 文本块重叠大小
    
    Returns:
        DocumentParser: 对应的解析器实例
    """
    if file_type.lower() == 'txt':
        return TxtParser(chunk_size, chunk_overlap)
    elif file_type.lower() == 'md':
        return MarkdownParser(chunk_size, chunk_overlap)
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")


def parse_and_split_document(
    content: bytes, 
    file_type: str, 
    chunk_size: int = 500, 
    chunk_overlap: int = 50,
    split_mode: str = 'fixed'
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    解析文档并切分为文本块（便捷函数）
    
    Args:
        content: 文档内容（bytes）
        file_type: 文件类型（txt/md）
        chunk_size: 文本块大小
        chunk_overlap: 文本块重叠大小
        split_mode: 切分模式 ('fixed'|'paragraph'|'sentence'|'custom')
    
    Returns:
        tuple: (解析后的文本, 文本块列表)
    """
    parser = get_parser(file_type, chunk_size, chunk_overlap)
    text = parser.parse(content)
    chunks = parser.split_into_chunks(text, mode=split_mode)
    return text, chunks

