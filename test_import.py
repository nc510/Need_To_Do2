#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的Question模型导入功能
"""

import os
import sys
import django

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置Django设置模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'need_to_do.settings')

# 初始化Django
django.setup()

from quiz.models import Question
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_question_validation():
    """测试Question模型的验证功能"""
    logger.info("开始测试Question模型的验证功能...")
    
    # 测试用例1: 正常的选择题
    try:
        question1 = Question(
            type=1,  # 选择题
            content="这是一个测试题目",
            options={"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
            correct_answer="A",
            score=1
        )
        question1.clean()  # 调用clean方法进行验证
        question1.save()
        logger.info("测试用例1通过: 正常选择题导入成功")
    except Exception as e:
        logger.error(f"测试用例1失败: {str(e)}")
    
    # 测试用例2: 带空格的正确选项
    try:
        question2 = Question(
            type=1,  # 选择题
            content="这是一个带空格答案的测试题目",
            options={"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
            correct_answer="  B  ",  # 带空格的答案
            score=1
        )
        question2.clean()  # 调用clean方法进行验证
        question2.save()
        # 检查答案是否被正确标准化
        if question2.correct_answer == "B":
            logger.info("测试用例2通过: 带空格的正确选项被正确处理")
        else:
            logger.error(f"测试用例2失败: 答案未被正确标准化，当前值: {question2.correct_answer}")
    except Exception as e:
        logger.error(f"测试用例2失败: {str(e)}")
    
    # 测试用例3: 小写字母的正确选项
    try:
        question3 = Question(
            type=1,  # 选择题
            content="这是一个小写字母答案的测试题目",
            options={"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
            correct_answer="c",  # 小写字母答案
            score=1
        )
        question3.clean()  # 调用clean方法进行验证
        question3.save()
        # 检查答案是否被正确标准化为大写
        if question3.correct_answer == "C":
            logger.info("测试用例3通过: 小写字母答案被正确转换为大写")
        else:
            logger.error(f"测试用例3失败: 答案未被正确转换为大写，当前值: {question3.correct_answer}")
    except Exception as e:
        logger.error(f"测试用例3失败: {str(e)}")
    
    # 测试用例4: 不存在的答案（应该抛出ValidationError）
    try:
        question4 = Question(
            type=1,  # 选择题
            content="这是一个无效答案的测试题目",
            options={"A": "选项A", "B": "选项B", "C": "选项C", "D": "选项D"},
            correct_answer="E",  # 不存在的答案
            score=1
        )
        question4.clean()  # 调用clean方法进行验证
        question4.save()
        logger.error("测试用例4失败: 应该抛出ValidationError但没有抛出")
    except Exception as e:
        # 检查错误消息是否符合预期
        if "正确答案不在提供的选项中" in str(e):
            logger.info(f"测试用例4通过: 正确抛出ValidationError并包含预期的错误消息")
        else:
            logger.error(f"测试用例4失败: 抛出了错误，但消息不符合预期: {str(e)}")
    
    # 测试用例5: 判断题
    try:
        question5 = Question(
            type=2,  # 判断题
            content="这是一个判断题",
            options={},  # 空选项，应该被自动设置为默认选项
            correct_answer="正确",  # 中文答案
            score=1
        )
        question5.clean()  # 调用clean方法进行验证
        question5.save()
        # 检查答案是否被正确转换为选项键
        if question5.correct_answer == "A":
            logger.info("测试用例5通过: 判断题中文答案被正确转换")
        else:
            logger.error(f"测试用例5失败: 判断题答案未被正确转换，当前值: {question5.correct_answer}")
    except Exception as e:
        logger.error(f"测试用例5失败: {str(e)}")


if __name__ == "__main__":
    logger.info("开始测试修复后的导入功能...")
    test_question_validation()
    logger.info("测试完成!")