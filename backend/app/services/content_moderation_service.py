"""
内容安全审核服务
"""
from typing import Dict, List
from sqlalchemy.orm import Session


class ContentModerationService:
    """内容审核服务"""
    
    def __init__(self, db: Session = None):
        self.db = db
        # 作弊关键词
        self.cheating_keywords = [
            '答案', '作业答案', '考试答案',
            '直接给我', '帮我做', '代码答案',
            '标准答案', '正确答案'
        ]
    
    async def check(self, content: str, content_type: str) -> Dict:
        """
        检查内容安全性
        
        Args:
            content: 待检查内容
            content_type: 'user_message' 或 'ai_response'
        
        Returns:
            {
                'status': 'pass' | 'warning' | 'blocked',
                'flags': [],
                'risk_score': 0-100,
                'reason': str,
                'sensitive_words_found': []
            }
        """
        flags = []
        risk_score = 0
        
        # 1. 敏感词检测
        found_words = await self._check_sensitive_words(content)
        if found_words:
            flags.append('sensitive_words')
            risk_score += 60  # ✅ 提高到60，直接触发拦截
        
        # 2. 作弊检测（仅用户消息）
        if content_type == 'user_message':
            if self._check_cheating(content):
                flags.append('asking_for_answers')
                risk_score += 30
        
        # 3. 长度检查
        if len(content) > 2000:
            flags.append('too_long')
            risk_score += 10
        
        # 4. 判断状态
        if risk_score >= 60:
            status = 'blocked'
        elif risk_score >= 30:
            status = 'warning'
        else:
            status = 'pass'
        
        return {
            'status': status,
            'flags': flags,
            'risk_score': risk_score,
            'reason': self._get_reason(flags),
            'sensitive_words_found': found_words
        }
    
    async def _check_sensitive_words(self, content: str) -> List[str]:
        """检测敏感词"""
        from app.models.learning_assistant import SensitiveWord
        
        found = []
        
        if self.db:
            # 从数据库加载敏感词
            sensitive_words = self.db.query(SensitiveWord).filter(
                SensitiveWord.is_active == 1
            ).all()
            
            content_lower = content.lower()
            for sw in sensitive_words:
                if sw.word in content_lower:
                    found.append(sw.word)
        
        return found
    
    def _check_cheating(self, content: str) -> bool:
        """检测作弊意图"""
        content_lower = content.lower()
        for keyword in self.cheating_keywords:
            if keyword in content_lower:
                return True
        return False
    
    def _get_reason(self, flags: List[str]) -> str:
        """获取原因说明"""
        reasons = {
            'sensitive_words': '包含敏感词汇',
            'asking_for_answers': '检测到可能的作弊意图',
            'too_long': '内容过长'
        }
        return '、'.join([reasons.get(f, f) for f in flags]) if flags else ''

