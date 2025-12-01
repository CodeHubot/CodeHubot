#!/usr/bin/env python3
"""
通过API手动触发文档向量化
使用HTTP请求调用后端API接口
"""
import requests
import sys


def get_api_url(kb_uuid, doc_uuid):
    """获取API URL"""
    # 修改为您的实际后端地址和端口
    base_url = "http://localhost:8000"  
    return f"{base_url}/api/kb-documents/{kb_uuid}/{doc_uuid}/embed"


def trigger_embedding(kb_uuid, doc_uuid, token=None):
    """触发文档向量化"""
    url = get_api_url(kb_uuid, doc_uuid)
    
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    
    data = {
        "force": False
    }
    
    print(f"🔄 正在触发向量化...")
    print(f"   知识库UUID: {kb_uuid}")
    print(f"   文档UUID: {doc_uuid}")
    print(f"   API URL: {url}")
    
    try:
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ 成功: {result.get('message', '向量化任务已提交')}")
            return True
        else:
            print(f"\n❌ 失败: HTTP {response.status_code}")
            try:
                error = response.json()
                print(f"   错误信息: {error.get('message', '未知错误')}")
            except:
                print(f"   响应内容: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ 请求失败: {str(e)}")
        return False


def print_usage():
    """打印使用说明"""
    print("""
📖 使用说明:

python scripts/trigger_embedding_api.py <知识库UUID> <文档UUID> [访问令牌]

参数说明:
  知识库UUID: 文档所属的知识库UUID
  文档UUID: 要向量化的文档UUID
  访问令牌: (可选) 如果需要认证，提供JWT token

示例:
  python scripts/trigger_embedding_api.py abc123 def456
  python scripts/trigger_embedding_api.py abc123 def456 eyJhbGc...

💡 提示:
  1. 确保后端服务正在运行
  2. 如果使用不同的端口，请修改脚本中的 base_url
  3. 可以在浏览器开发者工具中获取访问令牌
    """)


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)
    
    kb_uuid = sys.argv[1]
    doc_uuid = sys.argv[2]
    token = sys.argv[3] if len(sys.argv) > 3 else None
    
    success = trigger_embedding(kb_uuid, doc_uuid, token)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

