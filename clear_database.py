#!/usr/bin/env python
# 数据库清理脚本 - 清空所有数据但保留超级用户sky510

import os
import django
from django.db import connection

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'need_to_do.settings')
django.setup()

from django.contrib.auth.models import User
from quiz.models import Question, TestPaper, Profile, AnswerRecord, TestRecord, WrongQuestion

def clear_database():
    """清空数据库，保留超级用户sky510"""
    print("开始清理数据库...")
    
    # 保存超级用户sky510的信息
    try:
        superuser = User.objects.get(username='sky510', is_superuser=True)
        print(f"找到超级用户: {superuser.username}")
        preserve_superuser = True
    except User.DoesNotExist:
        print("警告: 未找到超级用户sky510")
        preserve_superuser = False
    
    # 按依赖关系顺序删除数据
    
    # 重置自增计数器的辅助函数
    def reset_auto_increment(table_name):
        with connection.cursor() as cursor:
            # MySQL语法
            cursor.execute(f'ALTER TABLE {table_name} AUTO_INCREMENT = 1')
            print(f"已重置 {table_name} 表的自增计数器")
    # 先删除Quiz应用中的所有数据
    print("删除AnswerRecord表...")
    AnswerRecord.objects.all().delete()
    reset_auto_increment('quiz_answerrecord')
    
    print("删除WrongQuestion表...")
    WrongQuestion.objects.all().delete()
    reset_auto_increment('quiz_wrongquestion')
    
    print("删除TestRecord表...")
    TestRecord.objects.all().delete()
    reset_auto_increment('quiz_testrecord')
    
    # 删除TestPaper和Question之间的多对多关系
    print("清理TestPaper和Question之间的关联...")
    for paper in TestPaper.objects.all():
        paper.questions.clear()
    
    print("删除TestPaper表...")
    TestPaper.objects.all().delete()
    reset_auto_increment('quiz_testpaper')
    
    print("删除Question表...")
    Question.objects.all().delete()
    reset_auto_increment('quiz_question')
    
    # 保存Profile相关联的超级用户信息
    if preserve_superuser:
        try:
            profile = Profile.objects.get(user=superuser)
            print(f"找到超级用户的Profile记录")
        except Profile.DoesNotExist:
            profile = None
            print("超级用户没有关联的Profile记录")
    else:
        profile = None
    
    print("删除Profile表...")
    Profile.objects.all().delete()
    reset_auto_increment('quiz_profile')
    
    # 删除所有用户，但保留超级用户sky510
    print("删除普通用户...")
    users_to_delete = User.objects.exclude(username='sky510')
    count = users_to_delete.count()
    users_to_delete.delete()
    print(f"已删除 {count} 个普通用户")
    
    # 重新创建超级用户的Profile记录（如果存在）
    if preserve_superuser and profile:
        print("重新创建超级用户的Profile记录...")
        Profile.objects.create(user=superuser, approval_status=profile.approval_status)
    
    print("数据库清理完成！")
    
    # 打印当前数据库状态
    print("\n当前数据库状态:")
    print(f"- 用户数: {User.objects.count()}")
    print(f"- 题目数: {Question.objects.count()}")
    print(f"- 试卷数: {TestPaper.objects.count()}")
    print(f"- 答题记录数: {AnswerRecord.objects.count()}")
    print(f"- 测试记录数: {TestRecord.objects.count()}")
    print(f"- 错题记录数: {WrongQuestion.objects.count()}")
    print(f"- 用户资料数: {Profile.objects.count()}")

if __name__ == "__main__":
    print("直接执行数据库清理操作...")
    clear_database()