#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置工作人员权限脚本
创建staff用户组并分配适当的权限
"""

import os
import sys
import django

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'need_to_do.settings')

# 初始化Django
django.setup()

from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from quiz.models import Question, TestPaper, Profile, TestRecord, AnswerRecord, WrongQuestion

def setup_staff_group():
    """
    创建staff用户组并分配适当的权限
    """
    print("开始设置工作人员权限...")
    
    # 创建或获取staff用户组
    staff_group, created = Group.objects.get_or_create(name='staff')
    if created:
        print("创建了新的staff用户组")
    else:
        print("找到现有的staff用户组")
    
    # 清除现有的权限，重新分配
    staff_group.permissions.clear()
    print("已清除staff用户组的现有权限")
    
    # 获取所有模型的ContentType
    question_content_type = ContentType.objects.get_for_model(Question)
    testpaper_content_type = ContentType.objects.get_for_model(TestPaper)
    profile_content_type = ContentType.objects.get_for_model(Profile)
    testrecord_content_type = ContentType.objects.get_for_model(TestRecord)
    answerrecord_content_type = ContentType.objects.get_for_model(AnswerRecord)
    wrongquestion_content_type = ContentType.objects.get_for_model(WrongQuestion)
    
    # 设置Question模型的权限（查看、编辑和添加，但不删除）
    question_view_perm = Permission.objects.get(
        content_type=question_content_type,
        codename='view_question'
    )
    question_change_perm = Permission.objects.get(
        content_type=question_content_type,
        codename='change_question'
    )
    question_add_perm = Permission.objects.get(
        content_type=question_content_type,
        codename='add_question'
    )
    
    # 设置TestPaper模型的权限（查看、编辑和添加，但不删除）
    testpaper_view_perm = Permission.objects.get(
        content_type=testpaper_content_type,
        codename='view_testpaper'
    )
    testpaper_change_perm = Permission.objects.get(
        content_type=testpaper_content_type,
        codename='change_testpaper'
    )
    testpaper_add_perm = Permission.objects.get(
        content_type=testpaper_content_type,
        codename='add_testpaper'
    )
    
    # 设置Profile模型的权限（查看、编辑和添加，但不删除）
    profile_view_perm = Permission.objects.get(
        content_type=profile_content_type,
        codename='view_profile'
    )
    profile_change_perm = Permission.objects.get(
        content_type=profile_content_type,
        codename='change_profile'
    )
    profile_add_perm = Permission.objects.get(
        content_type=profile_content_type,
        codename='add_profile'
    )
    
    # 设置TestRecord模型的权限（仅查看）
    testrecord_view_perm = Permission.objects.get(
        content_type=testrecord_content_type,
        codename='view_testrecord'
    )
    
    # 设置AnswerRecord模型的权限（仅查看）
    answerrecord_view_perm = Permission.objects.get(
        content_type=answerrecord_content_type,
        codename='view_answerrecord'
    )
    
    # 设置WrongQuestion模型的权限（仅查看）
    wrongquestion_view_perm = Permission.objects.get(
        content_type=wrongquestion_content_type,
        codename='view_wrongquestion'
    )
    
    # 将权限添加到用户组
    permissions_to_add = [
        # Question权限
        question_view_perm,
        question_change_perm,
        question_add_perm,
        # TestPaper权限
        testpaper_view_perm,
        testpaper_change_perm,
        testpaper_add_perm,
        # Profile权限
        profile_view_perm,
        profile_change_perm,
        profile_add_perm,
        # 记录类权限（仅查看）
        testrecord_view_perm,
        answerrecord_view_perm,
        wrongquestion_view_perm,
    ]
    
    staff_group.permissions.add(*permissions_to_add)
    print(f"已为staff用户组分配{len(permissions_to_add)}个权限")
    
    # 显示分配的权限
    print("\n已分配的权限列表：")
    for perm in staff_group.permissions.all():
        print(f"- {perm.content_type.model}: {perm.name}")
    
    # 查找所有is_staff=True但不是superuser的用户，并将其添加到staff组
    staff_users = User.objects.filter(is_staff=True, is_superuser=False)
    if staff_users.exists():
        print(f"\n找到{staff_users.count()}个工作人员用户，将其添加到staff组")
        for user in staff_users:
            user.groups.add(staff_group)
            print(f"- {user.username} 已添加到staff组")
    else:
        print("\n未找到需要添加到staff组的用户")
    
    print("\n工作人员权限设置完成！")
    print("提示：")
    print("1. 新创建的工作人员用户需要设置 is_staff=True 并添加到staff组")
    print("2. 工作人员将只能查看和编辑指定的模型，不能删除数据")
    print("3. 如需调整权限，请修改此脚本并重新运行")

if __name__ == '__main__':
    setup_staff_group()