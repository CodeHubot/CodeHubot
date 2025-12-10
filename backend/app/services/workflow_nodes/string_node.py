"""
字符串处理节点执行器
处理字符串数据 - 简化版本，更易用
"""
import logging
import re
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
            - operation: 操作类型（template/concat/replace/split/substring/trim/upper/lower/regex）
            - template: 模板字符串（支持变量替换）- 用于template操作
            - input: 输入字符串（支持变量替换）- 用于其他操作
            - 其他操作特定参数
        execution_context: 执行上下文
        replace_variables: 变量替换函数
        
    Returns:
        Dict[str, Any]: 节点输出，包含丰富的字段供后续使用
    """
    # 获取节点配置
    operation = node_data.get("operation", "template")
    
    # 对于不同的操作类型，使用不同的输入方式
    if operation == "template":
        # 模板模式：直接使用template字段
        template = node_data.get("template", "")
        input_text = replace_variables(template)
    else:
        # 其他操作：使用input字段
        input_text = node_data.get("input", "")
        input_text = replace_variables(input_text)
    
    # 根据操作类型执行相应操作
    result = None
    result_list = []  # 用于split等返回列表的操作
    
    if operation == "template":
        # 模板模式：input_text已经过变量替换
        result = input_text
        
    elif operation == "concat":
        # 拼接字符串
        separator = node_data.get("separator", "")
        texts = node_data.get("texts", "")  # 多行文本，每行一个
        if texts:
            text_list = [line.strip() for line in texts.split('\n') if line.strip()]
            processed_list = [replace_variables(t) for t in text_list]
            result = separator.join(processed_list)
        else:
            result = input_text
        
    elif operation == "replace":
        # 替换文本
        find = node_data.get("find", "")
        replace_with = node_data.get("replace_with", "")
        replace_all = node_data.get("replace_all", True)
        case_sensitive = node_data.get("case_sensitive", True)
        
        if not case_sensitive:
            # 不区分大小写
            pattern = re.compile(re.escape(find), re.IGNORECASE)
            if replace_all:
                result = pattern.sub(replace_with, input_text)
            else:
                result = pattern.sub(replace_with, input_text, count=1)
        else:
            if replace_all:
                result = input_text.replace(find, replace_with)
            else:
                result = input_text.replace(find, replace_with, 1)
        
    elif operation == "split":
        # 分割字符串
        separator = node_data.get("separator", ",")
        max_split = node_data.get("max_split", -1)
        
        if max_split > 0:
            result_list = input_text.split(separator, max_split)
        else:
            result_list = input_text.split(separator)
        
        # 清理空白
        result_list = [s.strip() for s in result_list]
        result = separator.join(result_list)  # 同时提供字符串形式
        
    elif operation == "substring":
        # 截取字符串
        start = node_data.get("start", 0)
        end = node_data.get("end", None)
        
        if end is None or end == 0:
            result = input_text[start:]
        else:
            result = input_text[start:end]
        
    elif operation == "trim":
        # 去除首尾空格
        result = input_text.strip()
        
    elif operation == "upper":
        # 转大写
        result = input_text.upper()
        
    elif operation == "lower":
        # 转小写
        result = input_text.lower()
        
    elif operation == "regex":
        # 正则表达式提取
        pattern = node_data.get("pattern", "")
        group = node_data.get("group", 0)
        find_all = node_data.get("find_all", False)
        
        if not pattern:
            raise ValueError("正则表达式提取需要配置pattern")
        
        if find_all:
            # 查找所有匹配
            matches = re.findall(pattern, input_text)
            result_list = matches if isinstance(matches, list) else [matches]
            result = str(result_list)
        else:
            # 查找第一个匹配
            match = re.search(pattern, input_text)
            if match:
                if group == 0:
                    result = match.group(0)
                else:
                    result = match.group(group) if group <= match.lastindex else ""
            else:
                result = ""
    
    else:
        raise ValueError(f"不支持的字符串操作类型: {operation}")
    
    # 构造输出结果
    output = {
        "result": result if result is not None else "",
        "text": result if result is not None else "",  # 别名
        "length": len(result) if result else 0,
        "is_empty": not bool(result),
        "operation": operation
    }
    
    # 如果有列表结果（split、regex等）
    if result_list:
        output["list"] = result_list
        output["count"] = len(result_list)
        output["first"] = result_list[0] if result_list else ""
        output["last"] = result_list[-1] if result_list else ""
    
    logger.info(f"字符串处理节点执行成功，操作: {operation}, 结果长度: {output['length']}")
    
    return output

