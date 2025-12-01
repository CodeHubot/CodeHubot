"""
查询扩展工具
为智能家居等场景的查询添加同义词和场景词，提高检索匹配率
"""
from typing import List, Dict, Set
import re


class QueryExpander:
    """查询扩展器"""
    
    def __init__(self):
        # 智能家居场景同义词映射
        self.smart_home_synonyms = {
            '睡觉': ['休息', '小睡', '打盹', '午睡', '就寝', '入睡', '想睡', '困了', '要睡'],
            '休息': ['睡觉', '小睡', '打盹', '放松', '歇息'],
            '工作': ['学习', '办公', '专注', '写作业', '做作业', '干活'],
            '学习': ['工作', '办公', '专注', '写作业', '做作业'],
            '放松': ['休闲', '娱乐', '休息', '想放松', '想休息'],
            '热': ['温度高', '闷热', '炎热', '太热', '好热'],
            '冷': ['温度低', '寒冷', '凉', '太冷', '好冷'],
            '提神': ['清醒', '精神', '有精神', '不困'],
        }
        
        # 场景词映射
        self.scene_keywords = {
            '睡眠场景': ['睡觉', '休息', '小睡', '打盹', '午睡', '就寝', '入睡', '想睡', '困了'],
            '工作场景': ['工作', '学习', '办公', '专注', '写作业', '做作业'],
            '放松场景': ['放松', '休闲', '娱乐', '想放松'],
            '温度场景': ['热', '冷', '温度高', '温度低', '闷热', '寒冷'],
        }
    
    def expand_query(self, query: str, domain: str = 'smart_home') -> str:
        """
        扩展查询，添加同义词和场景词
        
        Args:
            query: 原始查询
            domain: 领域（smart_home等）
        
        Returns:
            str: 扩展后的查询
        """
        if domain != 'smart_home':
            return query
        
        expanded_terms = [query]
        query_lower = query.lower()
        
        # 添加同义词
        for key, synonyms in self.smart_home_synonyms.items():
            if key in query or key in query_lower:
                # 添加所有同义词
                for synonym in synonyms:
                    if synonym not in expanded_terms:
                        expanded_terms.append(synonym)
        
        # 添加场景词
        for scene, keywords in self.scene_keywords.items():
            if any(keyword in query or keyword in query_lower for keyword in keywords):
                if scene not in expanded_terms:
                    expanded_terms.append(scene)
        
        # 合并扩展词
        expanded_query = ' '.join(expanded_terms)
        
        return expanded_query
    
    def expand_query_for_embedding(self, query: str, domain: str = 'smart_home') -> str:
        """
        为向量化扩展查询（更智能的方式）
        
        将查询扩展为更完整的描述，而不是简单的同义词列表
        """
        if domain != 'smart_home':
            return query
        
        # 检测场景
        if any(word in query for word in ['睡觉', '休息', '小睡', '打盹', '午睡', '就寝', '入睡', '想睡', '困了']):
            return f"{query} 睡眠场景 休息 小睡 打盹"
        elif any(word in query for word in ['工作', '学习', '办公', '专注', '写作业', '做作业']):
            return f"{query} 工作场景 学习 办公 专注"
        elif any(word in query for word in ['放松', '休闲', '娱乐', '想放松']):
            return f"{query} 放松场景 休闲 娱乐"
        elif any(word in query for word in ['热', '温度高', '闷热', '炎热']):
            return f"{query} 温度场景 热 闷热"
        elif any(word in query for word in ['冷', '温度低', '寒冷', '凉']):
            return f"{query} 温度场景 冷 寒冷"
        
        return query


# 全局实例
_query_expander = None


def get_query_expander() -> QueryExpander:
    """获取查询扩展器实例（单例）"""
    global _query_expander
    if _query_expander is None:
        _query_expander = QueryExpander()
    return _query_expander


def expand_query(query: str, domain: str = 'smart_home', mode: str = 'embedding') -> str:
    """
    扩展查询的便捷函数
    
    Args:
        query: 原始查询
        domain: 领域
        mode: 扩展模式
            - 'embedding': 为向量化扩展（添加场景词和同义词）
            - 'keyword': 为关键词检索扩展（添加同义词列表）
    
    Returns:
        str: 扩展后的查询
    """
    expander = get_query_expander()
    
    if mode == 'embedding':
        return expander.expand_query_for_embedding(query, domain)
    else:
        return expander.expand_query(query, domain)

