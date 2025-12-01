"""
测试智能体知识库关联API
用于诊断 500 错误
"""
import sys
import os
from pathlib import Path

# 将项目根目录添加到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import httpx
import logging
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

async def test_agent_kb_association(
    base_url: str,
    agent_uuid: str,
    token: str
):
    """
    测试智能体知识库关联列表API
    """
    url = f"{base_url}/api/knowledge-bases/agents/{agent_uuid}/knowledge-bases"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    logger.info(f"🔍 开始测试智能体知识库关联API")
    logger.info(f"   URL: {url}")
    logger.info(f"   智能体UUID: {agent_uuid}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info("📡 发送请求...")
            response = await client.get(url, headers=headers)
            
            logger.info(f"📥 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("✅ 请求成功！")
                logger.info(f"   响应数据: {data}")
                
                if data.get("code") == 200:
                    kbs = data.get("data", {}).get("knowledge_bases", [])
                    logger.info(f"   关联的知识库数量: {len(kbs)}")
                    
                    if kbs:
                        logger.info("   知识库列表:")
                        for idx, kb in enumerate(kbs, 1):
                            logger.info(f"     {idx}. {kb.get('knowledge_base_name')} "
                                      f"(UUID: {kb.get('knowledge_base_uuid')}, "
                                      f"优先级: {kb.get('priority')}, "
                                      f"启用: {kb.get('is_enabled')})")
                    else:
                        logger.info("   该智能体未关联任何知识库")
                    
                    return True
                else:
                    logger.error(f"❌ 业务错误: {data.get('message')}")
                    return False
            
            elif response.status_code == 404:
                logger.error("❌ 智能体不存在或已删除")
                logger.error(f"   响应: {response.text}")
                return False
            
            elif response.status_code == 403:
                logger.error("❌ 权限不足，无法查看该智能体")
                logger.error(f"   响应: {response.text}")
                return False
            
            elif response.status_code == 500:
                logger.error("❌ 服务器内部错误 (500)")
                logger.error(f"   响应: {response.text}")
                logger.error("")
                logger.error("🔧 请检查后端日志，查看详细错误信息:")
                logger.error("   tail -f logs/backend.log | grep '智能体知识库'")
                return False
            
            else:
                logger.error(f"❌ 未知错误: HTTP {response.status_code}")
                logger.error(f"   响应: {response.text}")
                return False
    
    except httpx.TimeoutException:
        logger.error("❌ 请求超时")
        return False
    except httpx.RequestError as e:
        logger.error(f"❌ 请求错误: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ 发生未知错误: {e}", exc_info=True)
        return False

async def main():
    """主函数"""
    # 配置
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")
    TEST_TOKEN = os.getenv("TEST_JWT_TOKEN")
    TEST_AGENT_UUID = os.getenv("TEST_AGENT_UUID", "98327a40-b4f1-48bd-b0d7-af07601836c5")

    if not TEST_TOKEN:
        logger.error("❌ 请设置环境变量 TEST_JWT_TOKEN")
        logger.info("")
        logger.info("📝 获取token的方法:")
        logger.info("   1. 登录系统")
        logger.info("   2. F12 → Application → Local Storage → token")
        logger.info("   3. 复制token值")
        logger.info("   4. export TEST_JWT_TOKEN='your-token-here'")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("🧪 智能体知识库关联API测试")
    logger.info("=" * 60)
    logger.info("")
    
    success = await test_agent_kb_association(BASE_URL, TEST_AGENT_UUID, TEST_TOKEN)
    
    logger.info("")
    logger.info("=" * 60)
    if success:
        logger.info("✅ 测试通过！")
    else:
        logger.error("❌ 测试失败！")
        logger.error("")
        logger.error("🔍 排查建议:")
        logger.error("   1. 检查后端服务是否运行: ps aux | grep uvicorn")
        logger.error("   2. 检查数据库表: SHOW TABLES LIKE 'aiot_agent_knowledge_bases';")
        logger.error("   3. 查看后端日志: tail -f logs/backend.log")
        logger.error("   4. 检查智能体是否存在: SELECT * FROM aiot_agents WHERE uuid='xxx';")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

