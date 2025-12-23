#!/usr/bin/env python3
"""
诊断学校权限问题脚本
用于检查管理员账号的 school_id 是否正确关联
"""
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models.user import User
from app.models.school import School

def diagnose_school_permission():
    """诊断学校权限配置"""
    db = SessionLocal()
    
    try:
        print("=" * 80)
        print("学校权限诊断工具")
        print("=" * 80)
        print()
        
        # 1. 获取所有学校管理员
        school_admins = db.query(User).filter(
            User.role == 'school_admin',
            User.deleted_at == None
        ).all()
        
        print(f"📋 找到 {len(school_admins)} 个学校管理员账号:")
        print("-" * 80)
        
        for admin in school_admins:
            print(f"\n用户ID: {admin.id}")
            print(f"  用户名: {admin.username}")
            print(f"  姓名: {admin.name or admin.real_name or '未设置'}")
            print(f"  角色: {admin.role}")
            print(f"  工号: {admin.teacher_number or '未设置'}")
            print(f"  school_id: {admin.school_id}")
            
            if admin.school_id:
                # 查找对应的学校
                school = db.query(School).filter(School.id == admin.school_id).first()
                if school:
                    print(f"  ✅ 关联学校: {school.school_name} (代码: {school.school_code})")
                    print(f"     学校UUID: {school.uuid}")
                    print(f"     学校ID: {school.id}")
                else:
                    print(f"  ❌ 错误: school_id={admin.school_id} 但找不到对应的学校！")
            else:
                print(f"  ⚠️  警告: school_id 为 NULL - 这会导致权限检查失败！")
        
        print("\n" + "=" * 80)
        print("🏫 所有学校列表:")
        print("-" * 80)
        
        schools = db.query(School).all()
        for school in schools:
            print(f"\n学校ID: {school.id}")
            print(f"  学校名称: {school.school_name}")
            print(f"  学校代码: {school.school_code}")
            print(f"  学校UUID: {school.uuid}")
            print(f"  是否激活: {'是' if school.is_active else '否'}")
            print(f"  管理员用户ID: {school.admin_user_id or '未分配'}")
            
            # 检查是否有对应的管理员
            if school.admin_user_id:
                admin = db.query(User).filter(User.id == school.admin_user_id).first()
                if admin:
                    print(f"  管理员用户名: {admin.username}")
                    if admin.school_id != school.id:
                        print(f"  ⚠️  警告: 管理员的 school_id ({admin.school_id}) 与学校ID ({school.id}) 不匹配！")
                else:
                    print(f"  ❌ 错误: admin_user_id={school.admin_user_id} 但找不到对应的用户！")
        
        print("\n" + "=" * 80)
        print("💡 权限检查说明:")
        print("-" * 80)
        print("当学校管理员访问 /pbl/school/{school_uuid}/users 时：")
        print("1. 系统通过 school_uuid 查找学校，获得 school.id")
        print("2. 检查 current_admin.school_id == school.id")
        print("3. 如果不相等，返回 '无权限查看其他学校用户' 错误")
        print()
        print("🔧 解决方案:")
        print("如果管理员的 school_id 为 NULL 或不正确，请使用以下方法修复：")
        print("1. 手动执行 SQL: UPDATE core_users SET school_id=X WHERE id=Y")
        print("2. 或使用平台管理员账号，通过 /pbl/school/{uuid}/assign-admin 接口分配")
        print()
        
    except Exception as e:
        print(f"❌ 诊断过程中出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    diagnose_school_permission()

