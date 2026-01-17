#!/usr/bin/env python3
"""
将指定用户升级为平台管理员（platform_admin）
使用方法: python upgrade_to_admin.py <username>
"""
import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.user import User

def upgrade_user_to_admin(username: str):
    """将用户升级为平台管理员"""
    db: Session = SessionLocal()
    
    try:
        # 查找用户
        user = db.query(User).filter(User.username == username).first()
        
        if not user:
            print(f"❌ 错误：用户 '{username}' 不存在")
            return False
        
        # 检查当前角色
        print(f"📋 当前用户信息:")
        print(f"   用户名: {user.username}")
        print(f"   邮箱: {user.email}")
        print(f"   当前角色: {user.role}")
        
        if user.role == 'platform_admin':
            print(f"✅ 用户已经是平台管理员，无需升级")
            return True
        
        # 升级为平台管理员
        user.role = 'platform_admin'
        db.commit()
        
        print(f"")
        print(f"✅ 成功！用户 '{username}' 已升级为平台管理员")
        print(f"")
        print(f"现在该用户可以：")
        print(f"  - 修改 MQTT 服务器配置")
        print(f"  - 管理系统配置")
        print(f"  - 管理用户和学校")
        print(f"  - 访问所有管理功能")
        
        return True
        
    except Exception as e:
        print(f"❌ 升级失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def list_users():
    """列出所有用户"""
    db: Session = SessionLocal()
    
    try:
        users = db.query(User).all()
        
        if not users:
            print("❌ 数据库中没有用户")
            return
        
        print("\n📋 当前所有用户:")
        print(f"{'ID':<5} {'用户名':<20} {'邮箱':<30} {'角色':<20}")
        print("-" * 80)
        
        for user in users:
            print(f"{user.id:<5} {user.username:<20} {user.email or 'N/A':<30} {user.role:<20}")
        
        print("")
        
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  CodeHubot - 用户角色升级工具")
    print("=" * 60)
    print("")
    
    if len(sys.argv) < 2:
        print("用法: python upgrade_to_admin.py <username>")
        print("或者: python upgrade_to_admin.py --list  (列出所有用户)")
        print("")
        print("示例:")
        print("  python upgrade_to_admin.py admin")
        print("  python upgrade_to_admin.py --list")
        print("")
        
        # 自动列出所有用户
        list_users()
        sys.exit(1)
    
    if sys.argv[1] == "--list":
        list_users()
        sys.exit(0)
    
    username = sys.argv[1]
    success = upgrade_user_to_admin(username)
    
    sys.exit(0 if success else 1)
