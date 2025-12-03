"""
开始节点执行器
接收工作流输入参数，作为工作流的入口
"""
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)


async def execute_start_node(
    node_data: Dict[str, Any],
    execution_context: Dict[str, Any],
    replace_variables: Callable[[str], str]
) -> Dict[str, Any]:
    """
    执行开始节点
    
    Args:
        node_data: 节点配置数据
        execution_context: 执行上下文
        replace_variables: 变量替换函数
        
    Returns:
        Dict[str, Any]: 节点输出（工作流输入参数）
    """
    # 开始节点直接返回工作流输入参数
    input_data = execution_context.get("input", {})
    logger.info(f"开始节点输出: {input_data}")
    return input_data

