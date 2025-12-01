#!/usr/bin/env python3
"""
检查Token配置脚本
用于验证环境变量中的Token过期时间是否正确读取
"""

import os
import sys

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("=" * 60)
    print("Token配置检查")
    print("=" * 60)
    print()
    
    # 显示环境变量
    print("📋 环境变量:")
    access_token_env = os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '未设置')
    refresh_token_env = os.getenv('REFRESH_TOKEN_EXPIRE_MINUTES', '未设置')
    print(f"  ACCESS_TOKEN_EXPIRE_MINUTES = {access_token_env}")
    print(f"  REFRESH_TOKEN_EXPIRE_MINUTES = {refresh_token_env}")
    print()
    
    # 尝试加载配置
    try:
        from app.core.config import settings
        
        # 显示实际配置值
        print("⚙️  实际配置值:")
        print(f"  access_token_expire_minutes = {settings.access_token_expire_minutes} 分钟")
        print(f"  refresh_token_expire_minutes = {settings.refresh_token_expire_minutes} 分钟")
        print()
        
        # 检查是否使用了默认值
        if settings.access_token_expire_minutes == 15:
            print("⚠️  警告: Access Token 使用了默认值 15 分钟")
            print("   提示: 请检查环境变量 ACCESS_TOKEN_EXPIRE_MINUTES 是否正确设置")
            if access_token_env != '未设置':
                print(f"   环境变量已设置: {access_token_env}，但未生效")
                print("   可能原因:")
                print("     1. 服务未重启")
                print("     2. 环境变量名称不正确")
                print("     3. Docker 容器中环境变量未正确传递")
        else:
            print(f"✅ Access Token 配置正确: {settings.access_token_expire_minutes} 分钟")
            if access_token_env != '未设置' and str(settings.access_token_expire_minutes) != access_token_env:
                print(f"   ⚠️  环境变量值 ({access_token_env}) 与配置值不一致")
        
        if settings.refresh_token_expire_minutes == 45:
            print("⚠️  警告: Refresh Token 使用了默认值 45 分钟")
            print("   提示: 请检查环境变量 REFRESH_TOKEN_EXPIRE_MINUTES 是否正确设置")
            if refresh_token_env != '未设置':
                print(f"   环境变量已设置: {refresh_token_env}，但未生效")
                print("   可能原因:")
                print("     1. 服务未重启")
                print("     2. 环境变量名称不正确")
                print("     3. Docker 容器中环境变量未正确传递")
        else:
            print(f"✅ Refresh Token 配置正确: {settings.refresh_token_expire_minutes} 分钟")
            if refresh_token_env != '未设置' and str(settings.refresh_token_expire_minutes) != refresh_token_env:
                print(f"   ⚠️  环境变量值 ({refresh_token_env}) 与配置值不一致")
        
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        print()
        print("💡 提示:")
        print("   1. 请确保所有必需的环境变量都已设置")
        print("   2. 检查 .env 文件或 Docker 环境变量配置")
        print("   3. 如果使用 Docker，请重启容器以应用新的环境变量")
    
    print()
    print("=" * 60)
    print("检查完成")
    print("=" * 60)
    print()
    print("💡 如果配置未生效，请:")
    print("   1. 检查 docker/.env 文件中的 ACCESS_TOKEN_EXPIRE_MINUTES 和 REFRESH_TOKEN_EXPIRE_MINUTES")
    print("   2. 重启后端服务: docker-compose -f docker/docker-compose.prod.yml restart backend")
    print("   3. 查看后端日志确认配置值: docker-compose -f docker/docker-compose.prod.yml logs backend | grep 'Token有效期'")

if __name__ == "__main__":
    main()

