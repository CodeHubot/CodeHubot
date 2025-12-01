#!/usr/bin/env python3
"""
向量化功能诊断脚本
快速检查配置和环境是否正确
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

def check_python_version():
    """检查Python版本"""
    print("=" * 60)
    print("1. Python 版本检查")
    print("=" * 60)
    import sys
    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("✅ Python 版本符合要求（3.8+）")
        return True
    else:
        print("❌ Python 版本过低，需要 3.8 或更高版本")
        return False


def check_dependencies():
    """检查依赖包"""
    print("\n" + "=" * 60)
    print("2. 依赖包检查")
    print("=" * 60)
    
    required_packages = [
        'chardet',
        'httpx',
        'sqlalchemy',
        'fastapi',
    ]
    
    all_ok = True
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package:20} 已安装")
        except ImportError:
            print(f"❌ {package:20} 未安装")
            all_ok = False
    
    return all_ok


def check_env_variables():
    """检查环境变量"""
    print("\n" + "=" * 60)
    print("3. 环境变量检查")
    print("=" * 60)
    
    # 尝试加载 .env 文件
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("✅ 已加载 .env 文件")
    except ImportError:
        print("⚠️  python-dotenv 未安装，尝试直接读取环境变量")
    except Exception as e:
        print(f"⚠️  加载 .env 文件失败: {e}")
    
    # 检查 API Key
    api_key = os.getenv("DASHSCOPE_API_KEY") or os.getenv("QWEN_API_KEY")
    
    if api_key:
        masked_key = f"{api_key[:10]}...{api_key[-4:]}" if len(api_key) > 14 else "***"
        print(f"✅ API Key 已配置: {masked_key}")
        print(f"   长度: {len(api_key)} 字符")
        
        if not api_key.startswith('sk-'):
            print("⚠️  警告: API Key 通常以 'sk-' 开头")
        
        return True
    else:
        print("❌ API Key 未配置")
        print("   请设置环境变量: DASHSCOPE_API_KEY 或 QWEN_API_KEY")
        return False


def check_database():
    """检查数据库连接"""
    print("\n" + "=" * 60)
    print("4. 数据库连接检查")
    print("=" * 60)
    
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        # 测试查询
        from app.models.document import Document
        count = db.query(Document).count()
        
        print(f"✅ 数据库连接正常")
        print(f"   文档总数: {count}")
        
        # 检查待处理文档
        pending_count = db.query(Document).filter(
            Document.embedding_status.in_(['pending', 'failed']),
            Document.deleted_at.is_(None)
        ).count()
        
        print(f"   待处理文档: {pending_count}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {str(e)}")
        return False


def check_embedding_service():
    """检查Embedding服务"""
    print("\n" + "=" * 60)
    print("5. Embedding 服务检查")
    print("=" * 60)
    
    try:
        from app.services.embedding_service import get_embedding_service
        
        service = get_embedding_service()
        print(f"✅ Embedding 服务初始化成功")
        print(f"   提供商: 阿里云通义千问")
        
        return True
        
    except ValueError as e:
        print(f"❌ Embedding 服务初始化失败: {str(e)}")
        if "API密钥未设置" in str(e):
            print("\n💡 解决方案:")
            print("   1. 获取 API Key: https://dashscope.console.aliyun.com/apiKey")
            print("   2. 配置到 .env 文件: DASHSCOPE_API_KEY=sk-xxx...")
            print("   3. 重启服务")
        return False
    except Exception as e:
        print(f"❌ Embedding 服务检查失败: {str(e)}")
        import traceback
        print("\n详细错误:")
        print(traceback.format_exc())
        return False


def test_embedding_api():
    """测试Embedding API调用"""
    print("\n" + "=" * 60)
    print("6. Embedding API 测试")
    print("=" * 60)
    
    try:
        import asyncio
        from app.services.embedding_service import get_embedding_service
        
        service = get_embedding_service()
        
        # 测试单个文本
        test_text = "这是一个测试文本"
        print(f"测试文本: {test_text}")
        
        async def test():
            embedding = await service.embed_text(test_text)
            return embedding
        
        embedding = asyncio.run(test())
        
        if embedding and isinstance(embedding, list) and len(embedding) > 0:
            print(f"✅ API 调用成功")
            print(f"   向量维度: {len(embedding)}")
            print(f"   向量示例（前5维）: {embedding[:5]}")
            return True
        else:
            print(f"❌ API 返回数据异常")
            return False
            
    except Exception as e:
        print(f"❌ API 调用失败: {str(e)}")
        
        error_msg = str(e)
        if "Invalid API-key" in error_msg or "401" in error_msg:
            print("\n💡 API Key 无效，请检查:")
            print("   1. API Key 是否正确")
            print("   2. 是否已开通 DashScope 服务")
        elif "403" in error_msg or "quota" in error_msg.lower():
            print("\n💡 配额不足，请:")
            print("   1. 访问阿里云控制台充值")
            print("   2. 检查账户余额")
        elif "timeout" in error_msg.lower():
            print("\n💡 网络超时，请检查:")
            print("   1. 服务器网络连接")
            print("   2. 防火墙设置")
        
        import traceback
        print("\n详细错误:")
        print(traceback.format_exc())
        return False


def check_file_permissions():
    """检查文件权限"""
    print("\n" + "=" * 60)
    print("7. 文件权限检查")
    print("=" * 60)
    
    data_dir = Path("data/knowledge-bases")
    
    if not data_dir.exists():
        print(f"⚠️  数据目录不存在，尝试创建: {data_dir}")
        try:
            data_dir.mkdir(parents=True, exist_ok=True)
            print(f"✅ 数据目录创建成功")
        except Exception as e:
            print(f"❌ 数据目录创建失败: {e}")
            return False
    else:
        print(f"✅ 数据目录存在: {data_dir}")
    
    # 检查可写性
    test_file = data_dir / ".test_write"
    try:
        test_file.write_text("test")
        test_file.unlink()
        print(f"✅ 数据目录可写")
        return True
    except Exception as e:
        print(f"❌ 数据目录不可写: {e}")
        return False


def print_summary(results):
    """打印总结"""
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)
    
    all_pass = all(results.values())
    
    for check, passed in results.items():
        status = "✅" if passed else "❌"
        print(f"{status} {check}")
    
    print("\n" + "=" * 60)
    if all_pass:
        print("🎉 所有检查通过！")
        print("\n您可以尝试处理文档:")
        print("  python scripts/manual_embed_document.py all")
    else:
        print("⚠️  发现问题，请根据上述提示修复")
        print("\n常见解决方案:")
        print("  1. 安装缺失依赖: pip install -r requirements.txt")
        print("  2. 配置 API Key: vim .env")
        print("  3. 检查网络连接")
        print("  4. 查看详细日志: tail -f logs/app.log")
    print("=" * 60)


def main():
    """主函数"""
    print("\n🔍 向量化功能诊断工具\n")
    
    results = {}
    
    # 逐项检查
    results["Python 版本"] = check_python_version()
    results["依赖包"] = check_dependencies()
    results["环境变量"] = check_env_variables()
    results["数据库连接"] = check_database()
    results["Embedding 服务"] = check_embedding_service()
    results["文件权限"] = check_file_permissions()
    
    # API 测试（如果前面都通过）
    if results["环境变量"] and results["Embedding 服务"]:
        results["API 调用测试"] = test_embedding_api()
    else:
        print("\n⏭️  跳过 API 测试（前置检查未通过）")
    
    # 打印总结
    print_summary(results)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 诊断过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

