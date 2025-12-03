"""
字符串处理节点执行器
处理字符串数据
"""
import logging
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)


async def execute_string_node(
    node_data: Dict[str, Any],
    execution_context: Dict[str, Any],
    replace_variables: Callable[[str], str]
) -> Dict[str, Any]:
    """
    执行字符串处理节点
    
    Args:
        node_data: 节点配置数据，包含：
            - operation: 操作类型（concat/replace/substring/format/trim/upper/lower）
            - input_string: 输入字符串（支持变量替换）
            - operation_params: 操作参数（根据操作类型不同而不同）
        execution_context: 执行上下文
        replace_variables: 变量替换函数
        
    Returns:
        Dict[str, Any]: 节点输出，包含：
            - result: 处理后的字符串
    """
    # 获取节点配置
    operation = node_data.get("operation")
    input_string = node_data.get("input_string", "")
    operation_params = node_data.get("operation_params", {})
    
    if not operation:
        raise ValueError("字符串处理节点必须配置操作类型")
    
    # 对输入字符串进行变量替换
    input_string = replace_variables(input_string)
    
    # 根据操作类型执行相应操作
    result = None
    
    if operation == "concat":
        # 拼接字符串
        separator = operation_params.get("separator", "")
        strings = operation_params.get("strings", [])
        # 对每个字符串进行变量替换
        processed_strings = [replace_variables(s) for s in strings]
        result = separator.join(processed_strings)
        
    elif operation == "replace":
        # 替换文本
        old_text = operation_params.get("old_text", "")
        new_text = operation_params.get("new_text", "")
        count = operation_params.get("count", -1)  # -1表示替换所有
        if count == -1:
            result = input_string.replace(old_text, new_text)
        else:
            result = input_string.replace(old_text, new_text, count)
        
    elif operation == "substring":
        # 截取字符串
        start = operation_params.get("start", 0)
        end = operation_params.get("end", len(input_string))
        result = input_string[start:end]
        
    elif operation == "format":
        # 格式化字符串
        format_string = operation_params.get("format_string", "")
        format_args = operation_params.get("format_args", {})
        # 对格式化参数进行变量替换
        processed_args = {
            k: replace_variables(str(v)) if isinstance(v, str) else v
            for k, v in format_args.items()
        }
        result = format_string.format(**processed_args)
        
    elif operation == "trim":
        # 去空格
        result = input_string.strip()
        
    elif operation == "upper":
        # 转大写
        result = input_string.upper()
        
    elif operation == "lower":
        # 转小写
        result = input_string.lower()
        
    else:
        raise ValueError(f"不支持的字符串操作类型: {operation}")
    
    logger.info(f"字符串处理节点执行成功，操作: {operation}, 结果长度: {len(result)}")
    
    return {
        "result": result
    }

