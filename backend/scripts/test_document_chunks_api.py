#!/usr/bin/env python3
"""
测试文档文本块 API
用于验证文档详情查看功能是否正常
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.models.document import Document, DocumentChunk
from app.models.knowledge_base import KnowledgeBase
from sqlalchemy import func

def test_document_chunks():
    """测试文档文本块数据"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("测试文档文本块数据")
        print("=" * 60)
        
        # 1. 查找已向量化的文档
        docs = db.query(Document).filter(
            Document.embedding_status == 'completed',
            Document.deleted_at.is_(None)
        ).limit(5).all()
        
        if not docs:
            print("❌ 没有找到已完成向量化的文档")
            print("   请先上传并向量化一个文档")
            return False
        
        print(f"✅ 找到 {len(docs)} 个已向量化的文档\n")
        
        # 2. 检查每个文档的文本块
        for doc in docs:
            print(f"文档: {doc.title}")
            print(f"  UUID: {doc.uuid}")
            print(f"  文本块数: {doc.chunk_count}")
            
            # 查询实际的文本块
            chunks = db.query(DocumentChunk).filter(
                DocumentChunk.document_id == doc.id
            ).order_by(DocumentChunk.chunk_index).all()
            
            actual_count = len(chunks)
            print(f"  实际文本块: {actual_count}")
            
            if actual_count != doc.chunk_count:
                print(f"  ⚠️  警告：文本块数量不匹配！")
            
            if chunks:
                # 显示第一个文本块的信息
                first_chunk = chunks[0]
                print(f"\n  第一个文本块:")
                print(f"    ID: {first_chunk.id}")
                print(f"    UUID: {first_chunk.uuid}")
                print(f"    序号: {first_chunk.chunk_index}")
                print(f"    字符数: {first_chunk.char_count}")
                print(f"    Token数: {first_chunk.token_count}")
                print(f"    有向量: {first_chunk.embedding_vector is not None}")
                print(f"    内容预览: {first_chunk.content[:100]}...")
                
                # 检查 content 字段
                if not first_chunk.content:
                    print(f"    ❌ 错误：content 字段为空！")
                else:
                    print(f"    ✅ content 字段有数据")
                
                # 检查向量
                if first_chunk.embedding_vector is None:
                    print(f"    ⚠️  警告：embedding_vector 为空")
                else:
                    print(f"    ✅ 向量已生成")
            else:
                print(f"  ❌ 错误：没有找到文本块数据！")
            
            print()
        
        # 3. 统计信息
        total_chunks = db.query(func.count(DocumentChunk.id)).scalar()
        chunks_with_vector = db.query(func.count(DocumentChunk.id))\
            .filter(DocumentChunk.embedding_vector.isnot(None)).scalar()
        
        print(f"总计:")
        print(f"  文本块总数: {total_chunks}")
        print(f"  已向量化: {chunks_with_vector}")
        print(f"  未向量化: {total_chunks - chunks_with_vector}")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def test_api_response_format():
    """测试 API 响应格式"""
    from app.schemas.document_schema import DocumentChunkResponse
    from app.models.document import DocumentChunk
    
    db = SessionLocal()
    
    try:
        print("\n" + "=" * 60)
        print("测试 API 响应格式")
        print("=" * 60)
        
        # 获取一个文本块
        chunk = db.query(DocumentChunk).first()
        
        if not chunk:
            print("❌ 没有找到文本块数据")
            return False
        
        # 转换为响应格式
        chunk_dict = DocumentChunkResponse.from_orm(chunk).model_dump()
        chunk_dict['has_embedding'] = chunk.embedding_vector is not None
        
        print("\n响应数据格式:")
        for key, value in chunk_dict.items():
            if key == 'content':
                print(f"  {key}: {str(value)[:100]}... (长度: {len(str(value))})")
            elif key == 'embedding_vector':
                continue  # 太长，跳过
            else:
                print(f"  {key}: {value}")
        
        # 检查必需字段
        required_fields = ['id', 'uuid', 'content', 'chunk_index', 'char_count', 
                          'token_count', 'has_embedding', 'created_at']
        
        print("\n必需字段检查:")
        all_present = True
        for field in required_fields:
            present = field in chunk_dict
            status = "✅" if present else "❌"
            print(f"  {status} {field}")
            if not present:
                all_present = False
        
        if all_present:
            print("\n✅ 所有必需字段都存在")
            return True
        else:
            print("\n❌ 缺少某些必需字段")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


def main():
    """主函数"""
    print("文档文本块 API 测试\n")
    
    result1 = test_document_chunks()
    result2 = test_api_response_format()
    
    print("\n" + "=" * 60)
    if result1 and result2:
        print("✅ 所有测试通过！")
        print("\n后续操作:")
        print("  1. 重启后端服务")
        print("  2. 在前端查看文档详情")
        print("  3. 应该能看到文本块内容了")
        return 0
    else:
        print("❌ 部分测试失败")
        print("\n可能的原因:")
        print("  1. 数据库中没有已向量化的文档")
        print("  2. 文本块数据不完整")
        print("  3. Schema 定义有问题")
        return 1


if __name__ == '__main__':
    sys.exit(main())

