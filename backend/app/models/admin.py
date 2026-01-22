"""
Admin 模块 - 用户模型的别名
为了保持 PBL 模块代码的兼容性，这里从 user.py 导入 User 模型
并创建 Admin 别名用于管理员相关操作
"""
from .user import User

# Admin 是 User 的别名，用于管理员相关操作
# 实际上 User 模型已经包含了所有角色的支持（platform_admin, team_admin, teacher, student, individual）
Admin = User

# 导出给其他模块使用
__all__ = ['Admin', 'User']
