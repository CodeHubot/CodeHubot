#!/usr/bin/env python3
"""
手动触发文档向量化脚本
用于测试或紧急处理待向量化的文档
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.document import Document
from app.services.embedding_service import embed_document


def list_pending_documents():
    """列出所有待处理的文档"""
    db = SessionLocal()
    try:
        docs = db.query(Document).filter(
            Document.embedding_status.in_(['pending', 'failed']),
            Document.deleted_at.is_(None)
        ).all()
        
        if not docs:
            print("✅ 没有待处理的文档")
            return []
        
        print(f"\n📋 找到 {len(docs)} 个待处理的文档：\n")
        for i, doc in enumerate(docs, 1):
            status_icon = "⏸️" if doc.embedding_status == 'pending' else "❌"
            print(f"{i}. {status_icon} [{doc.id}] {doc.title}")
            print(f"   状态: {doc.embedding_status}")
            print(f"   UUID: {doc.uuid}")
            print(f"   知识库ID: {doc.knowledge_base_id}")
            if doc.embedding_error:
                print(f"   错误: {doc.embedding_error}")
            print()
        
        return docs
    finally:
        db.close()


async def process_document(document_id: int):
    """处理单个文档"""
    db = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            print(f"❌ 文档 {document_id} 不存在")
            return False
        
        print(f"\n🔄 开始处理文档: {doc.title}")
        print(f"   ID: {doc.id}")
        print(f"   UUID: {doc.uuid}")
        
        await embed_document(document_id, db)
        
        # 刷新状态
        db.refresh(doc)
        
        if doc.embedding_status == 'completed':
            print(f"✅ 文档处理成功!")
            print(f"   文本块数量: {doc.chunk_count}")
            return True
        else:
            print(f"❌ 文档处理失败!")
            print(f"   状态: {doc.embedding_status}")
            if doc.embedding_error:
                print(f"   错误: {doc.embedding_error}")
            return False
            
    except Exception as e:
        print(f"❌ 处理异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


async def process_all_pending():
    """处理所有待处理的文档"""
    docs = list_pending_documents()
    if not docs:
        return
    
    print(f"\n🚀 开始批量处理 {len(docs)} 个文档...\n")
    
    success_count = 0
    fail_count = 0
    
    for doc in docs:
        result = await process_document(doc.id)
        if result:
            success_count += 1
        else:
            fail_count += 1
        print("-" * 60)
    
    print(f"\n📊 处理完成:")
    print(f"   ✅ 成功: {success_count}")
    print(f"   ❌ 失败: {fail_count}")


async def main():
    """主函数"""
    if len(sys.argv) > 1:
        if sys.argv[1] == 'list':
            # 只列出待处理文档
            list_pending_documents()
        elif sys.argv[1] == 'all':
            # 处理所有待处理文档
            await process_all_pending()
        elif sys.argv[1].isdigit():
            # 处理指定ID的文档
            doc_id = int(sys.argv[1])
            await process_document(doc_id)
        else:
            print("❌ 无效的参数")
            print_usage()
    else:
        print_usage()


def print_usage():
    """打印使用说明"""
    print("""
📖 使用说明:

1. 列出所有待处理的文档:
   python scripts/manual_embed_document.py list

2. 处理所有待处理的文档:
   python scripts/manual_embed_document.py all

3. 处理指定ID的文档:
   python scripts/manual_embed_document.py <document_id>
   
示例:
   python scripts/manual_embed_document.py 123
    """)


if __name__ == '__main__':
    asyncio.run(main())

