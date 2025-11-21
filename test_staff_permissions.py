#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试staff用户权限设置脚本

该脚本用于验证staff用户组的权限配置是否正确应用，检查staff用户是否具有合适的查看和编辑权限，
但不能删除数据。
"""

import os
import sys
import django

# 添加项目根目录到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置DJANGO_SETTINGS_MODULE环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'need_to_do.settings')

# 初始化Django
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from quiz.models import Question, TestPaper, Profile, TestRecord, AnswerRecord, WrongQuestion

def test_staff_permissions():
    """测试staff用户组的权限配置"""
    print("="*60)
    print("      staff用户权限配置测试脚本      ")
    print("="*60)
    
    # 1. 检查staff用户组是否存在
    try:
        staff_group = Group.objects.get(name='staff')
        print(f"✓ 找到了staff用户组: {staff_group.name}")
        
        # 2. 列出staff用户组拥有的权限
        print("\n✓ staff用户组拥有的权限:")
        permissions = staff_group.permissions.all()
        if permissions:
            for perm in permissions:
                print(f"  - {perm.name} ({perm.codename})")
        else:
            print("  - staff用户组没有分配任何权限")
    except Group.DoesNotExist:
        print("✗ 未找到staff用户组，请先运行set_staff_permissions.py脚本")
        return False
    
    # 3. 检查权限配置是否正确
    print("\n✓ 验证权限配置:")
    
    # 检查是否为Question, TestPaper, Profile分配了view和change权限
    expected_perms = [
        ('quiz', 'question', 'view_question'),
        ('quiz', 'question', 'change_question'),
        ('quiz', 'question', 'add_question'),
        ('quiz', 'testpaper', 'view_testpaper'),
        ('quiz', 'testpaper', 'change_testpaper'),
        ('quiz', 'testpaper', 'add_testpaper'),
        ('quiz', 'profile', 'view_profile'),
        ('quiz', 'profile', 'change_profile'),
        ('quiz', 'profile', 'add_profile'),
        ('quiz', 'testrecord', 'view_testrecord'),
        ('quiz', 'answerrecord', 'view_answerrecord'),
        ('quiz', 'wrongquestion', 'view_wrongquestion'),
    ]
    
    missing_perms = []
    for app_label, model, codename in expected_perms:
        try:
            perm = Permission.objects.get(codename=codename)
            if perm not in staff_group.permissions.all():
                missing_perms.append((app_label, model, codename))
        except Permission.DoesNotExist:
            missing_perms.append((app_label, model, codename))
    
    if missing_perms:
        print("  ✗ 缺少以下必要权限:")
        for app_label, model, codename in missing_perms:
            print(f"    - {app_label}.{model}.{codename}")
    else:
        print("  ✓ 所有必要的权限都已正确配置")
    
    # 4. 检查是否正确排除了删除权限
    delete_perms = [
        ('quiz', 'question', 'delete_question'),
        ('quiz', 'testpaper', 'delete_testpaper'),
        ('quiz', 'profile', 'delete_profile'),
        ('quiz', 'testrecord', 'delete_testrecord'),
        ('quiz', 'answerrecord', 'delete_answerrecord'),
        ('quiz', 'wrongquestion', 'delete_wrongquestion'),
    ]
    
    has_delete_perms = []
    for app_label, model, codename in delete_perms:
        try:
            perm = Permission.objects.get(codename=codename)
            if perm in staff_group.permissions.all():
                has_delete_perms.append((app_label, model, codename))
        except Permission.DoesNotExist:
            pass
    
    if has_delete_perms:
        print("  ✗ 发现staff用户组不应该具有的删除权限:")
        for app_label, model, codename in has_delete_perms:
            print(f"    - {app_label}.{model}.{codename}")
    else:
        print("  ✓ staff用户组没有配置任何删除权限，符合预期")
    
    # 5. 检查是否存在staff用户
    User = get_user_model()
    staff_users = User.objects.filter(is_staff=True, is_superuser=False)
    if staff_users.exists():
        print(f"\n✓ 发现{staff_users.count()}个staff用户:")
        for user in staff_users:
            # 检查用户是否在staff组中
            in_staff_group = user.groups.filter(name='staff').exists()
            group_status = "✓ 在staff组中" if in_staff_group else "✗ 不在staff组中"
            print(f"  - {user.username} ({user.email}) {group_status}")
    else:
        print("\n✗ 未找到任何staff用户")
        print("  提示: 您需要创建staff用户并设置is_staff=True")
    
    # 6. 总结
    print("\n="*30)
    print("      测试结果总结      ")
    print("="*30)
    
    if not missing_perms and not has_delete_perms:
        print("✓ 权限配置测试通过!")
        print("\n✓ staff用户现在应该能够:")
        print("  - 查看和编辑题目、试卷、用户资料等内容")
        print("  - 查看考试记录、答题记录和错题本")
        print("  - 导入新题目")
        print("✓ staff用户不能:")
        print("  - 删除任何数据")
        print("  - 编辑考试记录、答题记录等统计数据")
    else:
        print("✗ 权限配置测试未通过，请检查并修正权限设置")
    
    print("\n提示: 如需修复权限问题，请重新运行set_staff_permissions.py脚本")
    return True

if __name__ == '__main__':
    test_staff_permissions()