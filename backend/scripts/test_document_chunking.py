#!/usr/bin/env python3
"""
文档切分测试脚本
用于诊断向量化过程中的切分问题
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
import time

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

def test_chunking(file_path: str, split_mode: str = 'fixed', chunk_size: int = 500, chunk_overlap: int = 50):
    """测试文档切分"""
    from app.utils.document_parser import parse_and_split_document
    
    logger.info(f"=" * 60)
    logger.info(f"测试文件: {file_path}")
    logger.info(f"切分模式: {split_mode}")
    logger.info(f"块大小: {chunk_size}, 重叠: {chunk_overlap}")
    logger.info(f"=" * 60)
    
    # 读取文件
    file_path = Path(file_path)
    if not file_path.exists():
        logger.error(f"文件不存在: {file_path}")
        return False
    
    file_type = file_path.suffix.lstrip('.')
    logger.info(f"文件类型: {file_type}")
    
    with open(file_path, 'rb') as f:
        content = f.read()
    
    logger.info(f"文件大小: {len(content)} bytes")
    
    # 执行切分（带超时）
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("切分操作超时（30秒）")
    
    # 设置30秒超时
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(30)
    
    try:
        start_time = time.time()
        logger.info("开始切分...")
        
        text, chunks_data = parse_and_split_document(
            content,
            file_type,
            chunk_size,
            chunk_overlap,
            split_mode
        )
        
        elapsed = time.time() - start_time
        
        # 取消超时
        signal.alarm(0)
        
        logger.info(f"✅ 切分成功！")
        logger.info(f"   耗时: {elapsed:.2f} 秒")
        logger.info(f"   文本长度: {len(text)} 字符")
        logger.info(f"   文本块数: {len(chunks_data)} 个")
        
        if chunks_data:
            logger.info(f"\n前3个文本块预览:")
            for i, chunk in enumerate(chunks_data[:3]):
                logger.info(f"\n  块 {i+1}:")
                logger.info(f"    字符数: {chunk.get('char_count')}")
                logger.info(f"    Token数: {chunk.get('token_count')}")
                logger.info(f"    内容预览: {chunk.get('content', '')[:100]}...")
        
        return True
        
    except TimeoutError as e:
        logger.error(f"❌ {str(e)}")
        logger.error(f"   可能原因: 文件过大或切分算法陷入死循环")
        logger.error(f"   建议: 检查 document_parser.py 中的 _split_by_fixed_size 方法")
        return False
        
    except Exception as e:
        signal.alarm(0)  # 取消超时
        logger.error(f"❌ 切分失败: {str(e)}", exc_info=True)
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python test_document_chunking.py <文件路径> [split_mode] [chunk_size] [chunk_overlap]")
        print("")
        print("示例:")
        print("  python test_document_chunking.py data/knowledge-bases/.../xxx.txt")
        print("  python test_document_chunking.py data/knowledge-bases/.../xxx.txt paragraph")
        print("  python test_document_chunking.py data/knowledge-bases/.../xxx.txt fixed 500 50")
        sys.exit(1)
    
    file_path = sys.argv[1]
    split_mode = sys.argv[2] if len(sys.argv) > 2 else 'fixed'
    chunk_size = int(sys.argv[3]) if len(sys.argv) > 3 else 500
    chunk_overlap = int(sys.argv[4]) if len(sys.argv) > 4 else 50
    
    success = test_chunking(file_path, split_mode, chunk_size, chunk_overlap)
    
    if success:
        logger.info("\n✅ 测试通过！")
        sys.exit(0)
    else:
        logger.error("\n❌ 测试失败！")
        sys.exit(1)


if __name__ == '__main__':
    main()

