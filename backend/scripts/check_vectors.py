#!/usr/bin/env python3
"""
查看向量数据的脚本
"""
import sys
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.models.knowledge_base import KnowledgeBase
from sqlalchemy import func


def check_vectors():
    """检查向量数据"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("📊 向量数据检查报告")
        print("=" * 80)
        
        # 1. 统计已完成的文档
        completed_docs = db.query(Document).filter(
            Document.embedding_status == 'completed',
            Document.deleted_at.is_(None)
        ).all()
        
        print(f"\n✅ 已完成向量化的文档: {len(completed_docs)} 个\n")
        
        if not completed_docs:
            print("⚠️  没有已完成向量化的文档")
            return
        
        # 2. 显示每个文档的详情
        for doc in completed_docs:
            print(f"📄 文档 [{doc.id}] {doc.title}")
            print(f"   状态: {doc.embedding_status}")
            print(f"   文本块数量: {doc.chunk_count}")
            print(f"   向量化时间: {doc.embedded_at}")
            
            # 查询该文档的文本块
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == doc.id
            ).order_by(DocumentChunk.chunk_index).all()
            
            print(f"   实际文本块: {len(chunks)} 个")
            
            # 统计有向量的文本块
            chunks_with_vector = sum(1 for c in chunks if c.embedding_vector)
            print(f"   有向量的块: {chunks_with_vector} 个")
            
            if chunks:
                # 显示第一个文本块的信息
                first_chunk = chunks[0]
                print(f"\n   📝 文本块 #0 示例:")
                print(f"      内容（前100字）: {first_chunk.content[:100]}...")
                print(f"      字符数: {first_chunk.char_count}")
                print(f"      Token数: {first_chunk.token_count}")
                
                if first_chunk.embedding_vector:
                    vector = first_chunk.embedding_vector
                    if isinstance(vector, list):
                        print(f"      ✅ 向量维度: {len(vector)}")
                        print(f"      向量前5维: {vector[:5]}")
                    else:
                        print(f"      ⚠️  向量格式异常: {type(vector)}")
                else:
                    print(f"      ❌ 无向量数据")
            
            print()
        
        # 3. 全局统计
        print("=" * 80)
        print("📈 全局统计")
        print("=" * 80)
        
        total_docs = db.query(Document).filter(Document.deleted_at.is_(None)).count()
        total_chunks = db.query(DocumentChunk).count()
        chunks_with_vector = db.query(DocumentChunk).filter(
            DocumentChunk.embedding_vector.isnot(None)
        ).count()
        
        print(f"\n总文档数: {total_docs}")
        print(f"总文本块数: {total_chunks}")
        print(f"有向量的文本块: {chunks_with_vector}")
        if total_chunks > 0:
            print(f"向量化率: {chunks_with_vector * 100.0 / total_chunks:.2f}%")
        
        # 4. 按知识库统计
        print("\n" + "=" * 80)
        print("📚 按知识库统计")
        print("=" * 80 + "\n")
        
        kbs = db.query(KnowledgeBase).filter(KnowledgeBase.deleted_at.is_(None)).all()
        
        for kb in kbs:
            doc_count = db.query(Document).filter(
                Document.knowledge_base_id == kb.id,
                Document.deleted_at.is_(None)
            ).count()
            
            completed_count = db.query(Document).filter(
                Document.knowledge_base_id == kb.id,
                Document.embedding_status == 'completed',
                Document.deleted_at.is_(None)
            ).count()
            
            chunk_count = db.query(DocumentChunk).filter(
                DocumentChunk.knowledge_base_id == kb.id
            ).count()
            
            print(f"📚 {kb.name}")
            print(f"   文档数: {doc_count} (已完成: {completed_count})")
            print(f"   文本块数: {chunk_count}")
            print()
        
        print("=" * 80)
        print("✅ 检查完成")
        print("=" * 80)
        
    finally:
        db.close()


def show_chunk_detail(chunk_id: int):
    """显示特定文本块的详细信息"""
    db = SessionLocal()
    
    try:
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        
        if not chunk:
            print(f"❌ 文本块 {chunk_id} 不存在")
            return
        
        print("=" * 80)
        print(f"📝 文本块详情 [ID: {chunk_id}]")
        print("=" * 80)
        
        print(f"\n文档ID: {chunk.document_id}")
        print(f"知识库ID: {chunk.knowledge_base_id}")
        print(f"块索引: {chunk.chunk_index}")
        print(f"字符数: {chunk.char_count}")
        print(f"Token数: {chunk.token_count}")
        
        print(f"\n内容:")
        print("-" * 80)
        print(chunk.content)
        print("-" * 80)
        
        if chunk.embedding_vector:
            vector = chunk.embedding_vector
            if isinstance(vector, list):
                print(f"\n✅ 向量维度: {len(vector)}")
                print(f"向量类型: {type(vector[0]) if vector else 'N/A'}")
                print(f"\n向量数据（前10维）:")
                print(vector[:10])
                print(f"\n向量数据（后10维）:")
                print(vector[-10:])
            else:
                print(f"\n⚠️  向量格式异常: {type(vector)}")
        else:
            print(f"\n❌ 无向量数据")
        
        print("\n" + "=" * 80)
        
    finally:
        db.close()


def main():
    """主函数"""
    if len(sys.argv) > 1:
        # 显示特定文本块的详情
        try:
            chunk_id = int(sys.argv[1])
            show_chunk_detail(chunk_id)
        except ValueError:
            print("❌ 无效的文本块ID")
    else:
        # 显示总览
        check_vectors()


if __name__ == '__main__':
    main()

