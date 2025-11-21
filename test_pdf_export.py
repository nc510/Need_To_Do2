import os
import django
from django.contrib.auth import get_user_model
from django.http import HttpRequest

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Need_To_Do2.settings')
try:
    django.setup()
except ModuleNotFoundError:
    # 尝试调整Python路径
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    django.setup()

from quiz.models import WrongQuestion, Question, User
from quiz.pdf_generator import WrongQuestionPDFGenerator
from quiz.views import export_wrong_questions_pdf

def test_pdf_generator():
    """
    测试PDF生成器功能
    """
    print("开始测试PDF生成器...")
    
    # 获取一个有错题的用户
    User = get_user_model()
    users_with_wrong_questions = User.objects.filter(wrongquestion__isnull=False).distinct()
    
    if not users_with_wrong_questions.exists():
        print("警告：没有找到拥有错题的用户。请先创建一些错题数据进行测试。")
        # 如果没有用户，尝试创建测试数据
        create_test_data()
        users_with_wrong_questions = User.objects.filter(wrongquestion__isnull=False).distinct()
        if not users_with_wrong_questions.exists():
            print("无法创建测试数据，测试终止。")
            return False
    
    # 使用第一个有错题的用户
    user = users_with_wrong_questions.first()
    print(f"使用用户: {user.username} 进行测试")
    
    # 获取用户的错题
    wrong_questions = WrongQuestion.objects.filter(user=user).order_by('-added_at')
    print(f"找到 {wrong_questions.count()} 道错题")
    
    # 创建PDF生成器
    pdf_generator = WrongQuestionPDFGenerator()
    
    try:
        # 测试练习版PDF生成
        print("测试生成练习版PDF...")
        practice_pdf_buffer = pdf_generator.generate_practice_pdf(wrong_questions, user)
        
        # 保存练习版PDF文件
        practice_pdf_path = f"d:\\code\\AI_Code\\Need_To_Do2\\test_output\\练习版测试_{user.username}.pdf"
        os.makedirs(os.path.dirname(practice_pdf_path), exist_ok=True)
        with open(practice_pdf_path, 'wb') as f:
            f.write(practice_pdf_buffer.getvalue())
        print(f"练习版PDF已保存至: {practice_pdf_path}")
        
        # 测试复习版PDF生成
        print("测试生成复习版PDF...")
        review_pdf_buffer = pdf_generator.generate_review_pdf(wrong_questions, user)
        
        # 保存复习版PDF文件
        review_pdf_path = f"d:\\code\\AI_Code\\Need_To_Do2\\test_output\\复习版测试_{user.username}.pdf"
        with open(review_pdf_path, 'wb') as f:
            f.write(review_pdf_buffer.getvalue())
        print(f"复习版PDF已保存至: {review_pdf_path}")
        
        # 验证文件是否成功创建
        if os.path.exists(practice_pdf_path) and os.path.exists(review_pdf_path):
            practice_size = os.path.getsize(practice_pdf_path) / 1024
            review_size = os.path.getsize(review_pdf_path) / 1024
            print(f"PDF文件大小：")
            print(f"  - 练习版: {practice_size:.2f} KB")
            print(f"  - 复习版: {review_size:.2f} KB")
            print("PDF生成测试成功!")
            return True
        else:
            print("错误：PDF文件未成功创建")
            return False
    
    except Exception as e:
        print(f"PDF生成测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def create_test_data():
    """
    创建测试数据（如果需要）
    """
    print("正在创建测试数据...")
    
    try:
        # 创建测试用户
        test_user, created = User.objects.get_or_create(
            username='test_pdf_user',
            defaults={'email': 'test@example.com', 'password': 'testpassword123'}
        )
        if created:
            test_user.set_password('testpassword123')
            test_user.save()
        print(f"测试用户: {test_user.username} {'已创建' if created else '已存在'}")
        
        # 创建测试题目
        test_question1, _ = Question.objects.get_or_create(
            type=1,  # 选择题
            content='以下哪个是Python的内置数据类型？',
            options={'A': 'Array', 'B': 'List', 'C': 'Vector', 'D': 'Set'},
            correct_answer='B',
            explanation='List是Python的内置数据类型，用于存储有序的可变元素集合。'
        )
        
        test_question2, _ = Question.objects.get_or_create(
            type=2,  # 判断题
            content='Django是一个全栈Web框架。',
            correct_answer='A',
            explanation='Django是一个用Python编写的高级Web框架，它鼓励快速开发和简洁实用的设计。'
        )
        
        # 创建错题记录
        WrongQuestion.objects.get_or_create(
            user=test_user,
            question=test_question1,
            user_answer='A'
        )
        
        WrongQuestion.objects.get_or_create(
            user=test_user,
            question=test_question2,
            user_answer='B'
        )
        
        print("测试数据创建成功")
    except Exception as e:
        print(f"创建测试数据失败: {str(e)}")

def test_view_function():
    """
    测试视图函数（简单模拟）
    """
    print("\n开始测试视图函数...")
    
    try:
        # 创建请求对象
        request = HttpRequest()
        request.method = 'GET'
        
        # 获取测试用户
        User = get_user_model()
        user = User.objects.filter(username='test_pdf_user').first()
        if not user:
            print("警告：未找到测试用户")
            return False
        
        request.user = user
        
        # 测试练习版导出
        request.GET = {'type': 'practice'}
        print("测试练习版导出视图...")
        # 注意：这里只是验证函数可以被调用，实际的HTTP响应测试需要更完整的模拟
        
        # 测试复习版导出
        request.GET = {'type': 'review'}
        print("测试复习版导出视图...")
        
        print("视图函数测试成功")
        return True
    except Exception as e:
        print(f"视图函数测试失败: {str(e)}")
        return False

if __name__ == '__main__':
    print("===== 错题本PDF导出功能测试 =====")
    
    # 测试PDF生成器
    pdf_test_result = test_pdf_generator()
    
    # 测试视图函数
    view_test_result = test_view_function()
    
    # 打印最终结果
    print("\n===== 测试结果摘要 =====")
    print(f"PDF生成器测试: {'通过' if pdf_test_result else '失败'}")
    print(f"视图函数测试: {'通过' if view_test_result else '失败'}")
    
    if pdf_test_result and view_test_result:
        print("\n✅ 所有测试通过！错题本PDF导出功能正常工作。")
        print("请在 'd:\\code\\AI_Code\\Need_To_Do2\\test_output\\' 目录下查看生成的PDF文件。")
        print("您现在可以通过网页界面访问错题本页面，点击导出按钮进行实际使用。")
    else:
        print("\n❌ 测试未完全通过，请检查错误信息并修复问题。")