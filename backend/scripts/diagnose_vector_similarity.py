#!/usr/bin/env python3
"""
向量相似度诊断脚本
用于检查向量化和相似度计算是否正常
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import numpy as np
from app.core.database import SessionLocal
from app.models.document import DocumentChunk
from app.services.embedding_service import get_embedding_service
from dotenv import load_dotenv

load_dotenv()

async def diagnose():
    """诊断向量化和相似度计算"""
    db = SessionLocal()
    
    try:
        print("=" * 60)
        print("向量相似度诊断")
        print("=" * 60)
        
        # 1. 获取一个文档块
        chunk = db.query(DocumentChunk).filter(
            DocumentChunk.embedding_vector.isnot(None)
        ).first()
        
        if not chunk:
            print("❌ 没有找到已向量化的文档块")
            return
        
        print(f"\n测试文档块:")
        print(f"  ID: {chunk.id}")
        print(f"  内容: {chunk.content[:100]}...")
        print(f"  向量维度: {len(chunk.embedding_vector) if chunk.embedding_vector else 0}")
        
        # 2. 检查向量数据
        if not chunk.embedding_vector:
            print("❌ 向量为空")
            return
        
        vector = np.array(chunk.embedding_vector)
        print(f"\n向量统计:")
        print(f"  维度: {vector.shape}")
        print(f"  最小值: {vector.min():.6f}")
        print(f"  最大值: {vector.max():.6f}")
        print(f"  均值: {vector.mean():.6f}")
        print(f"  标准差: {vector.std():.6f}")
        print(f"  模长: {np.linalg.norm(vector):.6f}")
        
        # 3. 测试相同文本的向量化
        print(f"\n测试1: 相同文本的相似度（应该接近100%）")
        embedding_service = get_embedding_service()
        
        same_text_vector = await embedding_service.embed_text(chunk.content)
        
        if same_text_vector:
            same_text_vector = np.array(same_text_vector)
            similarity = np.dot(vector, same_text_vector) / (np.linalg.norm(vector) * np.linalg.norm(same_text_vector))
            print(f"  相似度: {similarity:.4f} ({similarity*100:.2f}%)")
            
            if similarity > 0.95:
                print(f"  ✅ 正常！相同文本相似度很高")
            elif similarity > 0.8:
                print(f"  ⚠️  有点低，但可能是模型特性")
            else:
                print(f"  ❌ 异常！相同文本相似度应该 > 0.95")
        else:
            print("  ❌ 向量化失败")
        
        # 4. 测试相关文本的相似度
        print(f"\n测试2: 相关文本的相似度")
        if "手机" in chunk.content or "ipad" in chunk.content.lower():
            related_query = "使用手机观看"
        else:
            related_query = "推荐使用"
        
        related_vector = await embedding_service.embed_text(related_query)
        
        if related_vector:
            related_vector = np.array(related_vector)
            similarity = np.dot(vector, related_vector) / (np.linalg.norm(vector) * np.linalg.norm(related_vector))
            print(f"  查询: {related_query}")
            print(f"  相似度: {similarity:.4f} ({similarity*100:.2f}%)")
            
            if similarity > 0.6:
                print(f"  ✅ 正常！相关文本相似度合理")
            elif similarity > 0.3:
                print(f"  ⚠️  偏低，可能需要优化查询方式")
            else:
                print(f"  ❌ 太低了，可能有问题")
        
        # 5. 测试完全不相关的文本
        print(f"\n测试3: 不相关文本的相似度（应该很低）")
        unrelated_query = "今天天气怎么样"
        
        unrelated_vector = await embedding_service.embed_text(unrelated_query)
        
        if unrelated_vector:
            unrelated_vector = np.array(unrelated_vector)
            similarity = np.dot(vector, unrelated_vector) / (np.linalg.norm(vector) * np.linalg.norm(unrelated_vector))
            print(f"  查询: {unrelated_query}")
            print(f"  相似度: {similarity:.4f} ({similarity*100:.2f}%)")
            
            if similarity < 0.3:
                print(f"  ✅ 正常！不相关文本相似度很低")
            elif similarity < 0.5:
                print(f"  ⚠️  有点高，但可能是模型特性")
            else:
                print(f"  ❌ 异常！不相关文本相似度不应该 > 0.5")
        
        # 6. 检查向量归一化
        print(f"\n测试4: 向量是否已归一化")
        norm = np.linalg.norm(vector)
        print(f"  向量模长: {norm:.6f}")
        
        if abs(norm - 1.0) < 0.01:
            print(f"  ✅ 向量已归一化")
        else:
            print(f"  ⚠️  向量未归一化，模长: {norm}")
            print(f"     这可能影响相似度计算")
        
        # 7. 测试用户的实际查询
        print(f"\n测试5: 用户实际查询")
        user_query = "如果用手机/ipad观看电子书的话，推荐什么？"
        
        user_vector = await embedding_service.embed_text(user_query)
        
        if user_vector:
            user_vector = np.array(user_vector)
            similarity = np.dot(vector, user_vector) / (np.linalg.norm(vector) * np.linalg.norm(user_vector))
            print(f"  查询: {user_query}")
            print(f"  相似度: {similarity:.4f} ({similarity*100:.2f}%)")
            
            # 检查文档内容是否包含相关关键词
            content_lower = chunk.content.lower()
            has_phone = "手机" in chunk.content or "ipad" in content_lower
            has_ebook = "电子书" in chunk.content or "epub" in content_lower
            
            print(f"\n  内容分析:")
            print(f"    包含'手机/ipad': {has_phone}")
            print(f"    包含'电子书/epub': {has_ebook}")
            
            if has_phone and has_ebook:
                print(f"    ✅ 内容完全匹配查询！")
                if similarity < 0.5:
                    print(f"    ❌ 但相似度太低（{similarity*100:.2f}%），这不正常！")
                    print(f"    可能原因:")
                    print(f"      1. Embedding模型不适合中文长文本")
                    print(f"      2. 查询文本过长")
                    print(f"      3. 向量化时的参数问题")
        
        print(f"\n" + "=" * 60)
        print(f"诊断完成")
        print(f"=" * 60)
        
    except Exception as e:
        print(f"❌ 诊断失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        db.close()


def main():
    """主函数"""
    print("向量相似度诊断工具\n")
    asyncio.run(diagnose())


if __name__ == '__main__':
    main()

