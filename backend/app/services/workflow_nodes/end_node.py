"""
结束节点执行器
收集执行结果，作为工作流的出口
"""
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)


async def execute_end_node(
    node_data: Dict[str, Any],
    execution_context: Dict[str, Any],
    replace_variables: Callable[[str], str]
) -> Dict[str, Any]:
    """
    执行结束节点
    
    Args:
        node_data: 节点配置数据
        execution_context: 执行上下文
        replace_variables: 变量替换函数
        
    Returns:
        Dict[str, Any]: 节点输出（收集所有节点输出）
    """
    # 结束节点收集所有节点输出（排除input）
    output = {
        node_id: output 
        for node_id, output in execution_context.items() 
        if node_id != "input"
    }
    logger.info(f"结束节点输出: {output}")
    return output

