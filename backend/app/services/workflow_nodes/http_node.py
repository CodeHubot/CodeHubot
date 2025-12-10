"""
HTTP请求节点执行器
调用外部HTTP API
"""
import logging
import asyncio
import json
import ssl
from typing import Dict, Any, Callable
import aiohttp

logger = logging.getLogger(__name__)


async def execute_http_node(
    node_data: Dict[str, Any],
    execution_context: Dict[str, Any],
    replace_variables: Callable[[str], str]
) -> Dict[str, Any]:
    """
    执行HTTP请求节点
    
    Args:
        node_data: 节点配置数据，包含：
            - url: 请求URL（支持变量替换）
            - method: 请求方法（GET/POST/PUT/DELETE等，默认GET）
            - headers: 请求头（可选，支持变量替换）
            - body: 请求体（可选，支持变量替换）
            - timeout: 超时时间（秒，默认10秒）
            - retryCount: 重试次数（默认0）
            - validateSSL: 是否验证SSL证书（默认True）
            - followRedirect: 是否跟随重定向（默认True）
        execution_context: 执行上下文
        replace_variables: 变量替换函数
        
    Returns:
        Dict[str, Any]: 节点输出，包含：
            - status_code: HTTP状态码
            - headers: 响应头
            - body: 响应体（JSON或文本）
    """
    # 获取节点配置
    url = node_data.get("url", "")
    method = node_data.get("method", "GET").upper()
    headers = node_data.get("headers", {})
    body = node_data.get("body")
    timeout = node_data.get("timeout", 10)
    retry_count = node_data.get("retryCount", 0)
    validate_ssl = node_data.get("validateSSL", True)
    follow_redirect = node_data.get("followRedirect", True)
    
    if not url:
        raise ValueError("HTTP节点必须配置URL")
    
    # 对URL、请求头、请求体进行变量替换
    url = replace_variables(url)
    
    # 替换请求头中的变量
    processed_headers = {}
    for key, value in headers.items():
        if isinstance(value, str):
            processed_headers[key] = replace_variables(value)
        else:
            processed_headers[key] = value
    
    # 替换请求体中的变量
    processed_body = None
    if body:
        if isinstance(body, str):
            processed_body = replace_variables(body)
            # 尝试解析为JSON
            try:
                processed_body = json.loads(processed_body)
            except json.JSONDecodeError:
                # 如果不是JSON，保持原样
                pass
        elif isinstance(body, dict):
            # 如果是字典，递归替换其中的字符串值
            processed_body = _replace_dict_variables(body, replace_variables)
        else:
            processed_body = body
    
    # 发送HTTP请求（支持重试）
    last_error = None
    for attempt in range(retry_count + 1):
        try:
            # 创建SSL上下文
            ssl_context = None
            if not validate_ssl:
                import ssl
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
            
            # 创建连接器配置
            connector = aiohttp.TCPConnector(ssl=ssl_context if not validate_ssl else None)
            
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=processed_headers,
                    json=processed_body if isinstance(processed_body, dict) else None,
                    data=processed_body if isinstance(processed_body, str) else None,
                    timeout=aiohttp.ClientTimeout(total=timeout),
                    allow_redirects=follow_redirect
                ) as response:
                    # 读取响应
                    try:
                        response_body = await response.json()
                    except:
                        response_body = await response.text()
                    
                    # 构造输出结果
                    output = {
                        "status_code": response.status,
                        "headers": dict(response.headers),
                        "body": response_body,
                        # 添加便捷访问字段
                        "data": response_body,  # 别名，方便引用
                        "status": response.status,  # 别名
                        "success": 200 <= response.status < 300,  # 成功标志
                        "url": url,  # 实际请求的URL（经过变量替换后）
                        "method": method  # 请求方法
                    }
                    
                    logger.info(f"HTTP节点执行成功，状态码: {response.status}, 尝试次数: {attempt + 1}/{retry_count + 1}")
                    return output
                    
        except asyncio.TimeoutError:
            last_error = TimeoutError(f"HTTP请求超时（{timeout}秒）")
            if attempt < retry_count:
                logger.warning(f"HTTP请求超时，正在重试 ({attempt + 1}/{retry_count})")
                await asyncio.sleep(1)  # 重试前等待1秒
            else:
                raise last_error
        except Exception as e:
            last_error = e
            if attempt < retry_count:
                logger.warning(f"HTTP请求失败: {str(e)}，正在重试 ({attempt + 1}/{retry_count})")
                await asyncio.sleep(1)  # 重试前等待1秒
            else:
                logger.error(f"HTTP节点执行失败（已重试{retry_count}次）: {str(e)}", exc_info=True)
                raise
    
    # 如果所有重试都失败，抛出最后一个错误
    if last_error:
        raise last_error


def _replace_dict_variables(data: Dict[str, Any], replace_variables: Callable[[str], str]) -> Dict[str, Any]:
    """递归替换字典中的变量"""
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = replace_variables(value)
        elif isinstance(value, dict):
            result[key] = _replace_dict_variables(value, replace_variables)
        elif isinstance(value, list):
            result[key] = [
                replace_variables(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            result[key] = value
    return result

