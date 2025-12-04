"""
工作流执行引擎
实现工作流的串行执行逻辑
"""
import logging
import re
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from app.schemas.workflow import WorkflowNode, WorkflowEdge, NodeExecutionResult
from app.utils.timezone import get_beijing_time_naive

logger = logging.getLogger(__name__)


class WorkflowExecutor:
    """工作流执行引擎"""
    
    def __init__(self):
        self.execution_context: Dict[str, Any] = {}
        self.node_results: Dict[str, NodeExecutionResult] = {}
        self.start_time: Optional[datetime] = None
    
    async def execute(
        self,
        nodes: List[WorkflowNode],
        edges: List[WorkflowEdge],
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        db_session=None
    ) -> Dict[str, Any]:
        """
        执行工作流
        
        Args:
            nodes: 节点列表
            edges: 边列表
            input_data: 工作流输入参数
            config: 工作流配置
            db_session: 数据库会话
            
        Returns:
            Dict[str, Any]: 执行结果，包含output和node_executions
        """
        self.start_time = get_beijing_time_naive()
        self.execution_context = {"input": input_data}
        self.node_results = {}
        
        try:
            # 1. 初始化执行上下文（包含输入参数）
            logger.info(f"开始执行工作流，输入参数: {input_data}")
            
            # 2. 计算节点执行顺序（使用拓扑排序）
            execution_order = self._get_execution_order(nodes, edges)
            logger.info(f"节点执行顺序: {[node.id for node in execution_order]}")
            
            # 3. 串行执行每个节点
            for node in execution_order:
                logger.info(f"执行节点: {node.id} ({node.type})")
                node_start_time = get_beijing_time_naive()
                
                try:
                    # 执行节点
                    node_output = await self._execute_node(node, db_session)
                    
                    # 保存节点输出到上下文
                    self.execution_context[node.id] = node_output
                    
                    # 记录节点执行结果
                    node_end_time = get_beijing_time_naive()
                    execution_time = int((node_end_time - node_start_time).total_seconds() * 1000)
                    
                    self.node_results[node.id] = NodeExecutionResult(
                        node_id=node.id,
                        node_type=node.type,
                        status="success",
                        output=node_output,
                        execution_time=execution_time,
                        started_at=node_start_time,
                        completed_at=node_end_time
                    )
                    
                    logger.info(f"节点 {node.id} 执行成功，耗时 {execution_time}ms")
                    
                except Exception as e:
                    # 节点执行失败
                    logger.error(f"节点 {node.id} 执行失败: {str(e)}", exc_info=True)
                    
                    node_end_time = get_beijing_time_naive()
                    execution_time = int((node_end_time - node_start_time).total_seconds() * 1000)
                    
                    self.node_results[node.id] = NodeExecutionResult(
                        node_id=node.id,
                        node_type=node.type,
                        status="failed",
                        error_message=str(e),
                        execution_time=execution_time,
                        started_at=node_start_time,
                        completed_at=node_end_time
                    )
                    
                    # 根据配置决定是否继续执行
                    continue_on_error = config.get("continue_on_error", False) if config else False
                    if not continue_on_error:
                        logger.error(f"节点执行失败，停止工作流执行")
                        break
            
            # 4. 收集最终输出（结束节点的输出）
            end_node = next((node for node in nodes if node.type == "end"), None)
            if end_node and end_node.id in self.execution_context:
                final_output = self.execution_context[end_node.id]
            else:
                # 如果没有结束节点输出，收集所有节点输出
                final_output = {node_id: output for node_id, output in self.execution_context.items() if node_id != "input"}
            
            # 5. 计算总执行时间
            end_time = get_beijing_time_naive()
            total_execution_time = int((end_time - self.start_time).total_seconds() * 1000)
            
            return {
                "output": final_output,
                "node_executions": [result.model_dump(mode='json') for result in self.node_results.values()],
                "execution_time": total_execution_time
            }
            
        except Exception as e:
            logger.error(f"工作流执行异常: {str(e)}", exc_info=True)
            raise
    
    def _replace_variables(self, text: str) -> str:
        """
        变量替换，支持以下格式：
        - {node_id} - 引用节点输出
        - {node_id.field} - 引用节点输出的特定字段
        - {input.param} - 引用工作流输入参数
        
        Args:
            text: 待替换的文本
            
        Returns:
            str: 替换后的文本
        """
        if not isinstance(text, str):
            return text
        
        # 匹配变量：{node_id} 或 {node_id.field} 或 {input.param}
        pattern = r'\{([^}]+)\}'
        
        def replace_match(match):
            var_path = match.group(1)
            
            # 处理 {input.param} 格式
            if var_path.startswith("input."):
                param_name = var_path[6:]  # 去掉 "input."
                value = self.execution_context.get("input", {}).get(param_name)
                if value is not None:
                    return str(value)
            
            # 处理 {node_id} 或 {node_id.field} 格式
            parts = var_path.split(".", 1)
            node_id = parts[0]
            
            if node_id in self.execution_context:
                node_output = self.execution_context[node_id]
                
                # 如果是 {node_id.field} 格式
                if len(parts) > 1:
                    field_path = parts[1]
                    # 支持嵌套字段访问，如 node_id.data.result
                    value = node_output
                    for field in field_path.split("."):
                        if isinstance(value, dict):
                            value = value.get(field)
                        else:
                            return match.group(0)  # 无法访问，返回原文本
                    if value is not None:
                        return str(value)
                else:
                    # {node_id} 格式，返回整个输出（如果是字符串）
                    if isinstance(node_output, str):
                        return node_output
                    elif isinstance(node_output, dict):
                        # 如果是字典，尝试转换为JSON字符串
                        import json
                        return json.dumps(node_output, ensure_ascii=False)
            
            # 变量未找到，返回原文本
            return match.group(0)
        
        result = re.sub(pattern, replace_match, text)
        return result
    
    def _get_execution_order(self, nodes: List[WorkflowNode], edges: List[WorkflowEdge]) -> List[WorkflowNode]:
        """
        使用拓扑排序计算节点执行顺序
        
        Args:
            nodes: 节点列表
            edges: 边列表
            
        Returns:
            List[WorkflowNode]: 按执行顺序排列的节点列表
        """
        # 构建邻接表和入度
        node_dict = {node.id: node for node in nodes}
        in_degree = {node.id: 0 for node in nodes}
        graph: Dict[str, List[str]] = {node.id: [] for node in nodes}
        
        for edge in edges:
            if edge.source in graph and edge.target in in_degree:
                graph[edge.source].append(edge.target)
                in_degree[edge.target] += 1
        
        # 拓扑排序
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            if current in node_dict:
                result.append(node_dict[current])
            
            for neighbor in graph.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result
    
    async def _execute_node(self, node: WorkflowNode, db_session) -> Dict[str, Any]:
        """
        根据节点类型调用对应的执行器
        
        Args:
            node: 节点对象
            db_session: 数据库会话
            
        Returns:
            Dict[str, Any]: 节点输出
        """
        from app.services.workflow_nodes import (
            execute_start_node,
            execute_llm_node,
            execute_http_node,
            execute_knowledge_node,
            execute_intent_node,
            execute_string_node,
            execute_end_node
        )
        
        node_type = node.type
        node_data = node.data or {}
        
        # 根据节点类型调用对应的执行器
        if node_type == "start":
            return await execute_start_node(node_data, self.execution_context, self._replace_variables)
        elif node_type == "llm":
            return await execute_llm_node(node_data, self.execution_context, self._replace_variables, db_session)
        elif node_type == "http":
            return await execute_http_node(node_data, self.execution_context, self._replace_variables)
        elif node_type == "knowledge":
            return await execute_knowledge_node(node_data, self.execution_context, self._replace_variables, db_session)
        elif node_type == "intent":
            return await execute_intent_node(node_data, self.execution_context, self._replace_variables, db_session)
        elif node_type == "string":
            return await execute_string_node(node_data, self.execution_context, self._replace_variables)
        elif node_type == "end":
            return await execute_end_node(node_data, self.execution_context, self._replace_variables)
        else:
            raise ValueError(f"不支持的节点类型: {node_type}")

