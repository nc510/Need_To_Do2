#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
非交互式创建Django超级用户脚本
"""

import os
import sys

# 添加Django项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'need_to_do.settings')

# 导入Django设置并初始化
import django
django.setup()

# 导入User模型
from django.contrib.auth.models import User


def create_superuser(username, email, password):
    """创建超级用户"""
    try:
        # 检查用户是否已存在
        if User.objects.filter(username=username).exists():
            print(f"用户 {username} 已存在，将更新密码")
            user = User.objects.get(username=username)
            user.set_password(password)
            user.email = email
            user.is_staff = True
            user.is_superuser = True
            user.save()
            print(f"用户 {username} 密码已更新")
        else:
            # 创建新的超级用户
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            user.save()
            print(f"超级用户 {username} 创建成功")
        return True
    except Exception as e:
        print(f"创建超级用户失败: {str(e)}")
        return False


if __name__ == "__main__":
    # 超级用户信息
    username = "sky510"
    email = "sky510@example.com"
    password = "sky510123"
    
    print(f"开始创建超级用户: {username}")
    create_superuser(username, email, password)
    print("操作完成！")