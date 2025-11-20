#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试Question模型的脚本，用于捕获详细的错误信息
"""

import os
import sys
import django

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 设置Django环境变量
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'need_to_do.settings')
django.setup()

# 导入必要的模型和模块
from quiz.models import Question
from django.core.exceptions import ValidationError
import traceback

def test_question_creation():
    """测试创建不同类型的Question实例"""
    print("开始测试Question模型...")
    
    # 测试用例1：有效选择题
    try:
        print("\n测试1: 创建有效选择题")
        q1 = Question(
            type=1,
            content="这是一个测试选择题",
            options={"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
            correct_answer="A",
            score=1,
            explanation="这是解析"
        )
        q1.full_clean()  # 运行所有验证器
        # q1.save()  # 实际保存时取消注释
        print("✓ 选择题验证通过")
    except ValidationError as e:
        print(f"✗ 选择题验证失败: {e.message_dict}")
        traceback.print_exc()
    except Exception as e:
        print(f"✗ 选择题创建异常: {str(e)}")
        traceback.print_exc()
    
    # 测试用例2：有效判断题
    try:
        print("\n测试2: 创建有效判断题")
        q2 = Question(
            type=2,
            content="这是一个测试判断题",
            options={"A": "正确", "B": "错误"},
            correct_answer="A",
            score=1,
            explanation="这是解析"
        )
        q2.full_clean()  # 运行所有验证器
        # q2.save()  # 实际保存时取消注释
        print("✓ 判断题验证通过")
    except ValidationError as e:
        print(f"✗ 判断题验证失败: {e.message_dict}")
        traceback.print_exc()
    except Exception as e:
        print(f"✗ 判断题创建异常: {str(e)}")
        traceback.print_exc()
    
    # 测试用例3：无效题型
    try:
        print("\n测试3: 创建无效题型")
        q3 = Question(
            type=3,  # 无效题型
            content="这是一个无效题型测试",
            options={"A": "选项A", "B": "选项B"},
            correct_answer="A",
            score=1
        )
        q3.full_clean()
        print("✗ 无效题型测试失败：应该抛出验证错误")
    except ValidationError as e:
        print(f"✓ 正确捕获无效题型错误: {e.message_dict}")
    except Exception as e:
        print(f"✗ 无效题型测试异常: {str(e)}")
        traceback.print_exc()
    
    # 测试用例4：选择题答案不在选项中
    try:
        print("\n测试4: 选择题答案不在选项中")
        q4 = Question(
            type=1,
            content="这是一个答案不在选项中的测试",
            options={"A": "选项A", "B": "选项B"},
            correct_answer="C",  # 不在选项中
            score=1
        )
        q4.full_clean()
        print("✗ 答案不在选项中测试失败：应该抛出验证错误")
    except ValidationError as e:
        print(f"✓ 正确捕获答案不在选项中错误: {e.message_dict}")
    except Exception as e:
        print(f"✗ 答案不在选项中测试异常: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    test_question_creation()
    print("\n测试完成。")