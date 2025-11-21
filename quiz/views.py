from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.db import IntegrityError
import datetime
import re
from django.contrib.auth.models import User
from quiz.models import Question, TestPaper, Profile, TestRecord, AnswerRecord, WrongQuestion

# 首页视图函数
def home(request):
    """首页视图，展示测试版本提示和试卷练习引导"""
    return render(request, 'quiz/frontend/home.html')

# 答题视图
def question_detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    if request.method == 'POST':
        user_answer = request.POST.get('answer')
        if user_answer == question.correct_answer:
            result = '正确'
        else:
            result = '错误'
        return render(request, 'quiz/frontend/answer_result.html', {
            'question': question,
            'user_answer': user_answer,
            'result': result,
            'correct_answer': question.correct_answer
        })
    return render(request, 'quiz/frontend/question_detail.html', {'question': question})

# 试卷列表视图（仅显示已发布的试卷）
def test_paper_list(request):
    test_papers = TestPaper.objects.filter(is_published=True).order_by('-created_at')
    # 实现分页，每页显示9套试卷
    paginator = Paginator(test_papers, 9)
    page_num = request.GET.get('page')
    try:
        paginated_test_papers = paginator.page(page_num)
    except PageNotAnInteger:
        # 如果页码不是整数，返回第一页
        paginated_test_papers = paginator.page(1)
    except EmptyPage:
        # 如果页码超出范围，返回最后一页
        paginated_test_papers = paginator.page(paginator.num_pages)
    return render(request, 'quiz/frontend/test_paper_list.html', {'test_papers': paginated_test_papers})

# 试卷详情视图
def test_paper_detail(request, paper_id):
    test_paper = get_object_or_404(TestPaper, pk=paper_id)
    # 确保只显示已发布的试卷
    if not test_paper.is_published:
        return redirect('test_paper_list')
    
    # 检查用户是否登录
    if not request.user.is_authenticated:
        # 未登录用户跳转到登录页面
        return redirect('login')
    
    # 检查用户是否已审核通过
    if request.user.profile.approval_status != 1:
        # 未审核或审核拒绝的用户跳转到审核页面
        return render(request, 'quiz/frontend/approval_pending.html', {
            'status': request.user.profile.get_approval_status_display()
        })
    
    return render(request, 'quiz/frontend/test_paper_detail.html', {'test_paper': test_paper})

# 试卷提交处理视图
@login_required
def submit_test_paper(request, paper_id):
    test_paper = get_object_or_404(TestPaper, pk=paper_id)
    
    # 检查用户是否已审核通过
    if request.user.profile.approval_status != 1:
        # 未审核或审核拒绝的用户跳转到审核页面
        return render(request, 'quiz/frontend/approval_pending.html', {
            'status': request.user.profile.get_approval_status_display()
        })
    
    if request.method == 'POST':
        total_score = 0
        user_answers = {}
        correct_count = 0
        question_results = []
        wrong_questions = []  # 用于收集错题
        
        # 收集用户答案并计算得分
        for question in test_paper.questions.all():
            question_num = question.id
            user_answer = request.POST.get(f'question_{question_num}')
            user_answers[question_num] = user_answer
            
            # 检查用户答案是否正确：忽略大小写并去除两端空格
            if user_answer and user_answer.strip().lower() == question.correct_answer.strip().lower():
                total_score += question.score
                correct_count += 1
                result = '正确'
            elif user_answer is None:
                result = '未答'  # 用户未回答
            else:
                result = '错误'
            
            question_results.append({
                'question': question,
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'result': result,
                'score': question.score
            })
        
        total_questions = test_paper.questions.count()
        wrong_count = total_questions - correct_count
        
        # 创建测试记录
        test_record = TestRecord.objects.create(
            user=request.user,
            test_paper=test_paper,
            score=total_score,
            total_score=test_paper.total_score
        )
        
        # 创建每题答题记录并收集错题
        for question in test_paper.questions.all():
            question_num = question.id
            user_answer = user_answers.get(question_num)
            
            # 检查用户答案是否正确
            if user_answer and user_answer.strip().lower() == question.correct_answer.strip().lower():
                is_correct = True
            else:
                is_correct = False
                # 收集错题
                if user_answer is not None:  # 用户已回答但错误
                    wrong_questions.append(question)
            
            # 创建答题记录
            AnswerRecord.objects.create(
                test_record=test_record,
                question=question,
                user_answer=user_answer,
                correct_answer=question.correct_answer,
                is_correct=is_correct,
                original_question_content=question.content,
                original_question_type=question.type,
                original_options=question.options,
                original_explanation=question.explanation
            )
        
        # 将错题添加到错题本
        for question in wrong_questions:
            # 查找该题对应的用户答案
            user_answer = user_answers.get(question.id)
            try:
                WrongQuestion.objects.create(user=request.user, question=question, user_answer=user_answer)
            except IntegrityError:
                # 如果错题已经存在于错题本中，更新用户答案
                wrong_question = WrongQuestion.objects.get(user=request.user, question=question)
                wrong_question.user_answer = user_answer
                wrong_question.save()
        
        return render(request, 'quiz/frontend/test_paper_result.html', {
            'test_paper': test_paper,
            'total_score': total_score,
            'user_answers': user_answers,
            'correct_count': correct_count,
            'wrong_count': wrong_count,
            'total_questions': total_questions,
            'question_results': question_results
        })
    return redirect('test_paper_detail', paper_id=paper_id)

# 注册视图
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        email = request.POST.get('email')
        name = request.POST.get('name')
        phone_number = request.POST.get('phone_number')
        qq_number = request.POST.get('qq_number')
        
        # 检查必填字段
        if not username or not password or not password_confirm or not email:
            messages.error(request, '请填写完整的注册信息')
            return render(request, 'quiz/frontend/register.html')
        
        # 验证密码一致性
        if password != password_confirm:
            messages.error(request, '两次输入的密码不一致')
            return render(request, 'quiz/frontend/register.html')
        
        # 验证手机号码格式
        if phone_number:
            phone_regex = re.compile(r'^1[3-9]\d{9}$')
            if not phone_regex.match(phone_number):
                messages.error(request, '手机号码格式不正确')
                return render(request, 'quiz/frontend/register.html')
            
            # 检查手机号码唯一性
            if Profile.objects.filter(phone_number=phone_number).exists():
                messages.error(request, '用户名或者手机号码已存在')
                return render(request, 'quiz/frontend/register.html')
        
        # 检查邮箱唯一性
        if User.objects.filter(email=email).exists():
            messages.error(request, '邮箱已存在')
            return render(request, 'quiz/frontend/register.html')
        
        try:
            # 创建用户
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email
            )
            
            # 保存姓名、手机号码和QQ号码到Profile
            if name:
                user.profile.name = name
            if phone_number:
                user.profile.phone_number = phone_number
            if qq_number:
                user.profile.qq_number = qq_number
            user.profile.save()
            
            messages.success(request, '注册成功，请等待管理员审核')
            return redirect('login')
        except IntegrityError:
            messages.error(request, '用户名或者手机号码akEMAIL已存在')
            return render(request, 'quiz/frontend/register.html')
    
    return render(request, 'quiz/frontend/register.html')

# 登录视图
def login_view(request):
    if request.method == 'POST':
        username_or_phone = request.POST.get('username')
        password = request.POST.get('password')
        
        # 首先尝试通过用户名登录
        user = authenticate(request, username=username_or_phone, password=password)
        
        # 如果用户名登录失败，尝试通过手机号码登录
        if user is None:
            try:
                # 通过手机号码查找对应的Profile
                profile = Profile.objects.get(phone_number=username_or_phone)
                # 获取对应的用户对象
                user = profile.user
                # 验证密码
                if user.check_password(password):
                    # 密码正确，登录用户
                    login(request, user)
                    messages.success(request, '登录成功')
                    return redirect('test_paper_list')
            except Profile.DoesNotExist:
                # 手机号码不存在
                pass
            except:
                # 其他错误
                pass
            
        # 如果两种方式都登录失败
        if user is None:
            messages.error(request, '用户名/手机号码或密码错误')
            return render(request, 'quiz/frontend/login.html')
        else:
            login(request, user)
            messages.success(request, '登录成功')
            return redirect('test_paper_list')
    
    return render(request, 'quiz/frontend/login.html')

# 退出登录视图
def logout_view(request):
    logout(request)
    messages.success(request, '已退出登录')
    return redirect('test_paper_list')

# 用户中心视图
@login_required
def user_center(request):
    # 获取用户的个人信息
    user = request.user
    profile = user.profile
    
    # 将User模型的last_login同步到Profile模型
    if user.last_login and (not profile.last_login or user.last_login > profile.last_login):
        profile.last_login = user.last_login
        profile.save()
    
    # 准备传递给模板的数据
    context = {
        'user': user,
        'profile': profile,
    }
    
    return render(request, 'quiz/frontend/user_center.html', context)

# 答题历史记录视图
@login_required
def test_history(request):
    # 获取当前用户的所有答题记录
    test_records = TestRecord.objects.filter(user=request.user).order_by('-completed_at')
    
    # 实现分页
    paginator = Paginator(test_records, 9)  # 每页显示9条记录
    page_num = request.GET.get('page')
    
    try:
        paginated_records = paginator.page(page_num)
    except PageNotAnInteger:
        paginated_records = paginator.page(1)
    except EmptyPage:
        paginated_records = paginator.page(paginator.num_pages)
    
    return render(request, 'quiz/frontend/test_history.html', {
        'test_records': paginated_records
    })

@login_required
def test_history_detail(request, record_id):
    # 获取答题记录
    test_record = get_object_or_404(TestRecord, pk=record_id)
    
    # 确保当前用户只能查看自己的答题记录
    if test_record.user != request.user:
        messages.error(request, '您没有权限查看此答题记录')
        return redirect('test_history')
    
    # 获取该答题记录的所有每题答题记录
    answer_records = AnswerRecord.objects.filter(test_record=test_record)
    
    return render(request, 'quiz/frontend/test_history_detail.html', {
        'test_record': test_record,
        'answer_records': answer_records
    })

# 错题本视图
@login_required
def wrong_question_notebook(request):
    # 获取当前用户的所有错题
    wrong_questions = WrongQuestion.objects.filter(user=request.user).order_by('-added_at')
    
    # 实现分页，每页显示50条错题
    paginator = Paginator(wrong_questions, 50)
    page_num = request.GET.get('page')
    
    try:
        paginated_wrong_questions = paginator.page(page_num)
    except PageNotAnInteger:
        paginated_wrong_questions = paginator.page(1)
    except EmptyPage:
        paginated_wrong_questions = paginator.page(paginator.num_pages)
    
    return render(request, 'quiz/frontend/wrong_question_notebook.html', {
        'wrong_questions': paginated_wrong_questions
    })

# 错题本组卷视图
@login_required
def create_wrong_question_paper(request):
    if request.method == 'POST':
        # 获取选中的题目ID列表
        selected_question_ids = request.POST.getlist('selected_questions')
        
        if not selected_question_ids:
            messages.error(request, '请至少选择一道错题')
            return redirect('wrong_question_notebook')
        
        # 获取当前用户选中的错题，按添加时间倒序排序
        wrong_questions = WrongQuestion.objects.filter(
            user=request.user,
            question_id__in=selected_question_ids
        ).order_by('-added_at')
    else:
        # 默认情况下显示所有错题
        wrong_questions = WrongQuestion.objects.filter(user=request.user).order_by('-added_at')
    
    if wrong_questions.count() == 0:
        messages.info(request, '您的错题本中没有题目')
        return redirect('wrong_question_notebook')
    
    return render(request, 'quiz/frontend/wrong_question_paper.html', {
        'wrong_questions': wrong_questions
    })

# 删除错题视图
@login_required
def delete_wrong_question(request, wrong_question_id):
    wrong_question = get_object_or_404(WrongQuestion, pk=wrong_question_id)
    # 检查是否是当前用户的错题
    if wrong_question.user == request.user:
        wrong_question.delete()
        messages.success(request, '错题已删除')
    else:
        messages.error(request, '您没有权限删除这道错题')
    return redirect('wrong_question_notebook')

# 错题本试卷提交视图
@login_required
def submit_wrong_question_paper(request):
    if request.method == 'POST':
        user_score = 0  # 用户实际得分
        total_possible_score = 0  # 总分（所有题目分数之和）
        correct_count = 0
        question_results = []
        
        # 获取所有题目ID
        question_ids = request.POST.getlist('question_id')
        
        for question_id in question_ids:
            question = get_object_or_404(Question, pk=question_id)
            total_possible_score += question.score  # 累加总分
            
            user_answer = request.POST.get(f'question_{question_id}')
            
            # 检查用户答案是否正确
            if user_answer and user_answer.strip().lower() == question.correct_answer.strip().lower():
                is_correct = True
                user_score += question.score  # 累加用户得分
                correct_count += 1
                result = '正确'
            elif user_answer is None:
                is_correct = False
                result = '未答'
            else:
                is_correct = False
                result = '错误'
            
            question_results.append({
                'question': question,
                'user_answer': user_answer,
                'correct_answer': question.correct_answer,
                'result': result,
                'score': question.score
            })
        
        total_questions = len(question_ids)
        wrong_count = total_questions - correct_count
        
        return render(request, 'quiz/frontend/wrong_question_paper_result.html', {
            'total_score': total_possible_score,
            'obtained_score': user_score,
            'correct_count': correct_count,
            'wrong_count': wrong_count,
            'total_questions': total_questions,
            'question_results': question_results
        })
    
    return redirect('create_wrong_question_paper')

# 错题本PDF导出视图
@login_required
def export_wrong_questions_pdf(request):
    from .pdf_generator import WrongQuestionPDFGenerator
    from django.http import HttpResponse
    from django.utils import timezone
    
    # 获取导出类型参数，默认为练习版
    export_type = request.GET.get('type', 'practice')
    
    # 验证导出类型参数
    if export_type not in ['practice', 'review']:
        messages.error(request, '无效的导出类型')
        return redirect('wrong_question_notebook')
    
    # 获取当前用户的所有错题，按添加时间倒序排序
    wrong_questions = WrongQuestion.objects.filter(user=request.user).order_by('-added_at')
    
    if not wrong_questions.exists():
        messages.info(request, '您的错题本中没有题目')
        return redirect('wrong_question_notebook')
    
    try:
        # 创建PDF生成器实例
        pdf_generator = WrongQuestionPDFGenerator()
        
        # 根据导出类型生成PDF
        if export_type == 'practice':
            pdf_buffer = pdf_generator.generate_practice_pdf(wrong_questions, request.user)
            # 生成日期时间格式的文件名：练习版_YYYYMMDD_HHMMSS.pdf
            export_time = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f'练习版_{export_time}.pdf'
        else:
            pdf_buffer = pdf_generator.generate_review_pdf(wrong_questions, request.user)
            # 生成日期时间格式的文件名：复习版_YYYYMMDD_HHMMSS.pdf
            export_time = timezone.now().strftime('%Y%m%d_%H%M%S')
            filename = f'复习版_{export_time}.pdf'
        
        # 创建HTTP响应，返回PDF文件
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
    except Exception as e:
        # 捕获所有可能的异常
        messages.error(request, f'PDF生成失败: {str(e)}')
        return redirect('wrong_question_notebook')

def home(request):
    """首页视图函数"""
    return render(request, 'quiz/frontend/home.html')
