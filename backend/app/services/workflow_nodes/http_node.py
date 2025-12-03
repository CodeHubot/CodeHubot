"""
HTTP请求节点执行器
调用外部HTTP API
"""
import logging
import asyncio
import json
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
    
    # 发送HTTP请求
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method,
                url=url,
                headers=processed_headers,
                json=processed_body if isinstance(processed_body, dict) else None,
                data=processed_body if isinstance(processed_body, str) else None,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                # 读取响应
                try:
                    response_body = await response.json()
                except:
                    response_body = await response.text()
                
                output = {
                    "status_code": response.status,
                    "headers": dict(response.headers),
                    "body": response_body
                }
                
                logger.info(f"HTTP节点执行成功，状态码: {response.status}")
                return output
                
    except asyncio.TimeoutError:
        raise TimeoutError(f"HTTP请求超时（{timeout}秒）")
    except Exception as e:
        logger.error(f"HTTP节点执行失败: {str(e)}", exc_info=True)
        raise


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

