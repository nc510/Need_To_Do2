import os
import sys
import django

# 设置Django环境
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'need_to_do.settings')
django.setup()

from quiz.models import Question
from django.core.exceptions import ValidationError
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_valid_cases():
    """测试有效的案例"""
    print("=== 测试有效的案例 ===")
    
    # 测试1: 正常的选择题，正确答案在选项中
    try:
        question = Question(
            type=1,
            content="测试题目1",
            options={"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
            correct_answer="A"
        )
        question.clean()
        print("✓ 测试1通过: 正常的选择题")
    except Exception as e:
        print(f"✗ 测试1失败: {e}")
    
    # 测试2: 带有空格的正确选项
    try:
        question = Question(
            type=1,
            content="测试题目2",
            options={"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
            correct_answer=" B "
        )
        question.clean()
        print("✓ 测试2通过: 带有空格的正确选项")
    except Exception as e:
        print(f"✗ 测试2失败: {e}")
    
    # 测试3: 小写字母的正确选项
    try:
        question = Question(
            type=1,
            content="测试题目3",
            options={"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
            correct_answer="b"
        )
        question.clean()
        print("✓ 测试3通过: 小写字母的正确选项")
    except Exception as e:
        print(f"✗ 测试3失败: {e}")
    
    # 测试4: 判断题
    try:
        question = Question(
            type=2,
            content="测试题目4",
            correct_answer="A"
        )
        question.clean()
        print("✓ 测试4通过: 判断题")
    except Exception as e:
        print(f"✗ 测试4失败: {e}")

def test_invalid_cases():
    """测试无效的案例"""
    print("\n=== 测试无效的案例 ===")
    
    # 测试5: 不存在的答案
    try:
        question = Question(
            type=1,
            content="测试题目5",
            options={"A": "选项A", "B": "选项B"},
            correct_answer="C"
        )
        question.clean()
        print("✗ 测试5失败: 不存在的答案应该抛出异常")
    except ValidationError as e:
        print(f"✓ 测试5通过: 正确捕获了不存在的答案: {e}")
    except Exception as e:
        print(f"✗ 测试5失败: 抛出了意外的异常: {e}")

def test_case_insensitive_matching():
    """测试大小写不敏感匹配"""
    print("\n=== 测试大小写不敏感匹配 ===")
    
    # 测试6: 选项键是小写字母的情况
    try:
        question = Question(
            type=1,
            content="测试题目6",
            options={"a": "选项A", "b": "选项B"},
            correct_answer="A"
        )
        question.clean()
        print("✓ 测试6通过: 大写答案匹配小写选项键")
    except Exception as e:
        print(f"✗ 测试6失败: {e}")
    
    # 测试7: 选项键是小写字母，答案是小写的情况
    try:
        question = Question(
            type=1,
            content="测试题目7",
            options={"a": "选项A", "b": "选项B"},
            correct_answer="a"
        )
        question.clean()
        print("✓ 测试7通过: 小写答案匹配小写选项键")
    except Exception as e:
        print(f"✗ 测试7失败: {e}")

if __name__ == "__main__":
    print("开始测试修复后的导入验证逻辑...\n")
    
    test_valid_cases()
    test_invalid_cases()
    test_case_insensitive_matching()
    
    print("\n测试完成！")