#!/usr/bin/env python3
"""
快速修复：直接处理所有待处理文档
不依赖后台任务，直接在主进程中执行
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 显式加载环境变量
from dotenv import load_dotenv
load_dotenv(override=True)  # 强制重新加载

import os
print(f"🔑 API Key 状态: {'已配置 ✅' if os.getenv('DASHSCOPE_API_KEY') else '未配置 ❌'}")
if os.getenv('DASHSCOPE_API_KEY'):
    key = os.getenv('DASHSCOPE_API_KEY')
    print(f"   前缀: {key[:10]}... 长度: {len(key)}")

from app.core.database import SessionLocal
from app.models.document import Document
from app.services.embedding_service import embed_document


async def process_all_pending():
    """处理所有待处理的文档"""
    db = SessionLocal()
    
    try:
        # 查询待处理文档
        docs = db.query(Document).filter(
            Document.embedding_status.in_(['pending', 'failed']),
            Document.deleted_at.is_(None)
        ).all()
        
        if not docs:
            print("\n✅ 没有待处理的文档")
            return
        
        print(f"\n📋 找到 {len(docs)} 个待处理的文档\n")
        
        success = 0
        failed = 0
        
        for doc in docs:
            print(f"🔄 处理文档 [{doc.id}] {doc.title}")
            
            try:
                # 直接在主进程中执行向量化
                await embed_document(doc.id, db)
                
                # 刷新状态
                db.refresh(doc)
                
                if doc.embedding_status == 'completed':
                    print(f"   ✅ 成功！文本块数: {doc.chunk_count}")
                    success += 1
                else:
                    print(f"   ❌ 失败: {doc.embedding_error}")
                    failed += 1
                    
            except Exception as e:
                print(f"   ❌ 异常: {str(e)}")
                failed += 1
            
            print()
        
        print("=" * 60)
        print(f"📊 处理完成: ✅ {success} 成功, ❌ {failed} 失败")
        print("=" * 60)
        
    finally:
        db.close()


if __name__ == '__main__':
    print("🚀 快速修复工具 - 直接处理待处理文档\n")
    asyncio.run(process_all_pending())

