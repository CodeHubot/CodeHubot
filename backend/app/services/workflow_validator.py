"""
工作流验证服务
实现DAG验证逻辑，包括循环检测、节点验证等
"""
import logging
from typing import List, Dict, Any, Set, Optional
from app.schemas.workflow import WorkflowNode, WorkflowEdge, ValidationResult

logger = logging.getLogger(__name__)


class WorkflowValidator:
    """工作流验证器"""
    
    @staticmethod
    def validate(nodes: List[WorkflowNode], edges: List[WorkflowEdge]) -> ValidationResult:
        """
        执行完整的工作流验证流程
        
        Args:
            nodes: 节点列表
            edges: 边列表
            
        Returns:
            ValidationResult: 验证结果
        """
        errors = []
        warnings = []
        
        # 1. 开始节点验证
        start_nodes = [node for node in nodes if node.type == 'start']
        if len(start_nodes) == 0:
            errors.append("工作流必须包含一个开始节点")
        elif len(start_nodes) > 1:
            errors.append(f"工作流只能包含一个开始节点，当前有{len(start_nodes)}个")
        
        # 2. 结束节点验证
        end_nodes = [node for node in nodes if node.type == 'end']
        if len(end_nodes) == 0:
            errors.append("工作流必须包含一个结束节点")
        elif len(end_nodes) > 1:
            errors.append(f"工作流只能包含一个结束节点，当前有{len(end_nodes)}个")
        
        # 如果缺少开始或结束节点，直接返回（后续验证需要这些节点）
        if len(start_nodes) != 1 or len(end_nodes) != 1:
            return ValidationResult(
                is_valid=False,
                errors=errors,
                warnings=warnings
            )
        
        # 3. 边有效性验证
        node_ids = {node.id for node in nodes}
        for edge in edges:
            if edge.source not in node_ids:
                errors.append(f"边 '{edge.id}' 的源节点 '{edge.source}' 不存在")
            if edge.target not in node_ids:
                errors.append(f"边 '{edge.id}' 的目标节点 '{edge.target}' 不存在")
        
        # 如果边无效，继续验证但记录错误
        if errors:
            # 继续验证其他项，但最终返回无效
        
        # 4. 循环依赖检测（DFS）
        cycle_detected = WorkflowValidator._detect_cycle(nodes, edges)
        if cycle_detected:
            errors.append("工作流中存在循环依赖，DAG必须是无环的")
        
        # 5. 节点可达性验证
        if not cycle_detected and not errors:
            unreachable_nodes = WorkflowValidator._find_unreachable_nodes(nodes, edges, start_nodes[0].id)
            if unreachable_nodes:
                warnings.append(f"以下节点从开始节点不可达: {', '.join(unreachable_nodes)}")
        
        # 6. 孤立节点检测（没有连接的节点）
        connected_nodes = set()
        for edge in edges:
            connected_nodes.add(edge.source)
            connected_nodes.add(edge.target)
        isolated_nodes = [node.id for node in nodes if node.id not in connected_nodes and node.type not in ['start', 'end']]
        if isolated_nodes:
            warnings.append(f"以下节点是孤立的（没有连接）: {', '.join(isolated_nodes)}")
        
        is_valid = len(errors) == 0
        
        return ValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def _detect_cycle(nodes: List[WorkflowNode], edges: List[WorkflowEdge]) -> bool:
        """
        使用DFS算法检测循环依赖
        
        Args:
            nodes: 节点列表
            edges: 边列表
            
        Returns:
            bool: 如果存在循环返回True，否则返回False
        """
        # 构建邻接表
        graph: Dict[str, List[str]] = {node.id: [] for node in nodes}
        for edge in edges:
            if edge.source in graph:
                graph[edge.source].append(edge.target)
        
        # DFS状态：0=未访问, 1=访问中, 2=已访问
        state: Dict[str, int] = {node.id: 0 for node in nodes}
        
        def dfs(node_id: str) -> bool:
            """DFS递归函数，返回True表示检测到循环"""
            if state[node_id] == 1:  # 访问中，说明存在环
                return True
            if state[node_id] == 2:  # 已访问，跳过
                return False
            
            state[node_id] = 1  # 标记为访问中
            
            # 遍历所有邻接节点
            for neighbor in graph.get(node_id, []):
                if dfs(neighbor):
                    return True
            
            state[node_id] = 2  # 标记为已访问
            return False
        
        # 对所有节点进行DFS
        for node in nodes:
            if state[node.id] == 0:
                if dfs(node.id):
                    return True
        
        return False
    
    @staticmethod
    def _find_unreachable_nodes(nodes: List[WorkflowNode], edges: List[WorkflowEdge], start_node_id: str) -> List[str]:
        """
        查找从开始节点不可达的节点
        
        Args:
            nodes: 节点列表
            edges: 边列表
            start_node_id: 开始节点ID
            
        Returns:
            List[str]: 不可达节点ID列表
        """
        # 构建邻接表（反向，用于从开始节点遍历）
        graph: Dict[str, List[str]] = {node.id: [] for node in nodes}
        for edge in edges:
            if edge.source in graph:
                graph[edge.source].append(edge.target)
        
        # 从开始节点进行BFS遍历
        visited: Set[str] = set()
        queue = [start_node_id]
        visited.add(start_node_id)
        
        while queue:
            current = queue.pop(0)
            for neighbor in graph.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        # 找出所有未访问的节点
        all_node_ids = {node.id for node in nodes}
        unreachable = all_node_ids - visited
        
        return list(unreachable)

