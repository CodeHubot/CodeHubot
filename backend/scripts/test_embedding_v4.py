#!/usr/bin/env python3
"""
测试 text-embedding-v4 
验证升级后的向量化服务是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import numpy as np
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

async def test_v4():
    """测试 v4 向量化服务"""
    from app.services.embedding_service import get_embedding_service
    
    print("=" * 60)
    print("text-embedding-v4 测试")
    print("=" * 60)
    
    # 获取服务
    service = get_embedding_service(force_new=True)  # 强制创建新实例
    
    print(f"\n服务信息:")
    print(f"  模型: {service.model_name}")
    print(f"  API: {service.base_url}")
    print(f"  维度: {service.dimension}")
    
    # 测试1：单个文本向量化
    print(f"\n" + "=" * 60)
    print("测试1：单个文本向量化")
    print("=" * 60)
    
    test_text = "如果用手机/ipad观看电子书的话，推荐什么？"
    print(f"输入: {test_text}")
    
    vector = await service.embed_text(test_text)
    
    if vector:
        vector_arr = np.array(vector)
        print(f"✅ 向量化成功")
        print(f"   维度: {len(vector)}")
        print(f"   类型: {type(vector)}")
        print(f"   最小值: {vector_arr.min():.6f}")
        print(f"   最大值: {vector_arr.max():.6f}")
        print(f"   均值: {vector_arr.mean():.6f}")
        print(f"   前5个值: {vector[:5]}")
    else:
        print("❌ 向量化失败")
        return False
    
    # 测试2：批量向量化
    print(f"\n" + "=" * 60)
    print("测试2：批量向量化")
    print("=" * 60)
    
    test_texts = [
        "手机看电子书推荐格式",
        "epub 格式适合 ipad",
        "kindle 用 mobi 格式"
    ]
    
    print(f"输入: {len(test_texts)} 个文本")
    for i, text in enumerate(test_texts, 1):
        print(f"  {i}. {text}")
    
    vectors = await service.embed_texts(test_texts)
    
    success_count = sum(1 for v in vectors if v is not None)
    
    if success_count == len(test_texts):
        print(f"✅ 批量向量化成功")
        print(f"   成功: {success_count}/{len(test_texts)}")
    else:
        print(f"⚠️  部分成功: {success_count}/{len(test_texts)}")
    
    # 测试3：相似度计算
    print(f"\n" + "=" * 60)
    print("测试3：相似度计算")
    print("=" * 60)
    
    query = "手机 电子书 格式"
    doc = "推荐您使用epub格式。epub可以下载个"掌阅"APP打开"
    
    print(f"查询: {query}")
    print(f"文档: {doc}")
    
    query_vec = await service.embed_text(query)
    doc_vec = await service.embed_text(doc)
    
    if query_vec and doc_vec:
        query_arr = np.array(query_vec)
        doc_arr = np.array(doc_vec)
        
        similarity = np.dot(query_arr, doc_arr) / (np.linalg.norm(query_arr) * np.linalg.norm(doc_arr))
        
        print(f"\n相似度: {similarity:.4f} ({similarity*100:.2f}%)")
        
        if similarity > 0.7:
            print("✅ 优秀！相似度很高")
        elif similarity > 0.5:
            print("✅ 良好！相似度合理")
        elif similarity > 0.3:
            print("⚠️  一般，相似度偏低")
        else:
            print("❌ 差，相似度太低")
    else:
        print("❌ 向量化失败，无法计算相似度")
    
    # 测试4：问句 vs 关键词
    print(f"\n" + "=" * 60)
    print("测试4：问句 vs 关键词效果对比")
    print("=" * 60)
    
    reference_doc = "推荐您使用epub格式。epub可以下载个"掌阅"APP打开，可以自由更改字体大小"
    
    test_queries = [
        ("问句形式", "如果用手机/ipad观看电子书的话，推荐什么？"),
        ("关键词形式", "手机 ipad 电子书 推荐"),
        ("简短问句", "手机看电子书用什么格式"),
    ]
    
    doc_vec = await service.embed_text(reference_doc)
    
    if doc_vec:
        doc_arr = np.array(doc_vec)
        
        print(f"参考文档: {reference_doc[:50]}...")
        print(f"\n测试不同查询方式:")
        
        for query_type, query_text in test_queries:
            query_vec = await service.embed_text(query_text)
            
            if query_vec:
                query_arr = np.array(query_vec)
                similarity = np.dot(query_arr, doc_arr) / (np.linalg.norm(query_arr) * np.linalg.norm(doc_arr))
                
                print(f"\n  {query_type}:")
                print(f"    查询: {query_text}")
                print(f"    相似度: {similarity:.4f} ({similarity*100:.2f}%)")
                
                if similarity > 0.6:
                    print(f"    ✅ 效果好")
                elif similarity > 0.4:
                    print(f"    ⚠️  效果一般")
                else:
                    print(f"    ❌ 效果差")
    
    print(f"\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    return True


def main():
    """主函数"""
    try:
        success = asyncio.run(test_v4())
        
        if success:
            print("\n✅ 所有测试通过！")
            print("\n后续步骤:")
            print("  1. 重启后端服务")
            print("  2. 在前端测试向量检索")
            print("  3. 对比升级前后的相似度")
            print("  4. 考虑重新向量化现有文档")
            return 0
        else:
            print("\n❌ 测试失败")
            return 1
            
    except Exception as e:
        print(f"\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())

