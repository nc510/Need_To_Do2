from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django import forms
from .models import Question, TestPaper, Profile, TestRecord, AnswerRecord, WrongQuestion
import pandas as pd
import json
import logging

# 配置日志记录
logger = logging.getLogger(__name__)

# 基础ModelAdmin类，为所有模型提供一致的权限控制
class BaseStaffAdmin(admin.ModelAdmin):
    """
    基础ModelAdmin类，为staff用户提供一致的权限控制
    staff用户可以查看和编辑，但不能删除数据
    """
    
    def has_view_permission(self, request, obj=None):
        """控制查看权限"""
        # 超级用户始终有查看权限
        if request.user.is_superuser:
            return True
        # staff用户需要有相应的view权限
        return request.user.has_perm(f'quiz.view_{self.model._meta.model_name}')
    
    def has_change_permission(self, request, obj=None):
        """控制编辑权限"""
        # 超级用户始终有编辑权限
        if request.user.is_superuser:
            return True
        # staff用户需要有相应的change权限
        return request.user.has_perm(f'quiz.change_{self.model._meta.model_name}')
    
    def has_delete_permission(self, request, obj=None):
        """控制删除权限 - 只有超级用户才能删除"""
        return request.user.is_superuser
    
    def has_add_permission(self, request):
        """控制添加权限"""
        # 超级用户始终有添加权限
        if request.user.is_superuser:
            return True
        # staff用户需要有相应的add权限
        return request.user.has_perm(f'quiz.add_{self.model._meta.model_name}')

class QuestionImportForm(forms.Form):
    excel_file = forms.FileField(label='Excel文件')

class ProfileAdmin(BaseStaffAdmin):
    list_display = ('user', 'approval_status', 'created_at', 'updated_at')
    list_filter = ('approval_status', 'created_at')
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)

class QuestionAdmin(BaseStaffAdmin):
    list_display = ('id', 'type', 'content', 'score', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('content', 'explanation')
    ordering = ('-created_at',)
    change_list_template = 'admin/quiz/question/change_list.html'
    actions = ['batch_delete_questions']  # 添加自定义批量删除动作
    
    def get_actions(self, request):
        """根据用户权限显示或隐藏动作"""
        actions = super().get_actions(request)
        # 只有超级用户才能看到批量删除动作
        if not request.user.is_superuser and 'batch_delete_questions' in actions:
            del actions['batch_delete_questions']
        return actions
    
    def batch_delete_questions(self, request, queryset):
        """批量删除题目，使用分批处理避免超时"""
        total_count = queryset.count()
        if total_count == 0:
            return
        
        # 每批删除的数量
        batch_size = 100
        deleted_count = 0
        
        # 分批删除
        from django.db import transaction
        from django.utils.translation import gettext as _
        
        try:
            # 获取所有要删除的题目ID
            all_ids = list(queryset.values_list('id', flat=True))
            
            # 按批次删除
            for i in range(0, len(all_ids), batch_size):
                batch_ids = all_ids[i:i+batch_size]
                # 使用事务确保每批删除的原子性
                with transaction.atomic():
                    # 先删除关联的记录（避免级联删除超时）
                    from .models import AnswerRecord, WrongQuestion, TestPaper
                    
                    # 删除相关的答题记录
                    AnswerRecord.objects.filter(question_id__in=batch_ids).delete()
                    
                    # 删除相关的错题记录
                    WrongQuestion.objects.filter(question_id__in=batch_ids).delete()
                    
                    # 从试卷中移除题目（避免多对多关系级联删除问题）
                    for test_paper in TestPaper.objects.all():
                        # 使用ID列表而不是QuerySet对象
                        test_paper.questions.remove(*Question.objects.filter(id__in=batch_ids))
                    
                    # 删除题目本身
                    batch_deleted = Question.objects.filter(id__in=batch_ids).delete()[0]
                    deleted_count += batch_deleted
                    
                    # 记录进度
                    logger.info(f'已删除 {deleted_count}/{total_count} 道题目')
            
            self.message_user(request, _(f'成功删除 {deleted_count} 道题目'))
        except Exception as e:
            logger.error(f'批量删除题目失败: {str(e)}')
            self.message_user(request, _(f'删除失败: {str(e)}'), level=messages.ERROR)
    
    batch_delete_questions.short_description = '分批删除选中的题目 (适合大量删除)'
    
    # 在管理界面添加批量导入按钮和处理导入逻辑
    def changelist_view(self, request, extra_context=None):
        # 只有明确是导入文件的POST请求才执行自定义逻辑
        # 所有其他POST请求（包括删除操作）都交给Django默认处理
        if request.method == 'POST' and 'excel_file' in request.FILES and '_selected_action' not in request.POST:
            import_form = QuestionImportForm(request.POST, request.FILES)
            if import_form.is_valid():
                excel_file = import_form.cleaned_data['excel_file']
                try:
                    # 解析Excel文件
                    df = pd.read_excel(excel_file)
                    
                    # 遍历每行数据，创建题目
                    for index, row in df.iterrows(): 
                        # Skip empty rows
                        if row.isnull().all():
                            continue
                        # 转换选项为JSON格式
                        options = {} 
                        # 检查中英文两种列名格式
                        for option_key in ['A', 'B', 'C', 'D']:
                            # 先检查中文列名（例如：选项A）
                            ch_column_name = f'选项{option_key}'
                            if ch_column_name in row and pd.notnull(row[ch_column_name]):
                                options[option_key] = row[ch_column_name]
                            # 再检查英文列名（例如：A）
                            elif option_key in row and pd.notnull(row[option_key]):
                                options[option_key] = row[option_key]
                            # 还可以检查其他可能的列名格式
                            elif f'Option {option_key}' in row and pd.notnull(row[f'Option {option_key}']):
                                options[option_key] = row[f'Option {option_key}']
                            elif f'option_{option_key}' in row and pd.notnull(row[f'option_{option_key}']):
                                options[option_key] = row[f'option_{option_key}']

                        # 处理题型：支持数字或字符串格式
                        question_type = row['题型']
                        try:
                            # 先尝试转换为整数
                            question_type_int = int(question_type)
                            # 验证是否是有效题型
                            if question_type_int not in [1, 2]:
                                raise ValueError(f"不支持的题型: {question_type_int}")
                        except ValueError:
                            # 如果转换失败，使用字符串映射
                            type_mapping = {
                                '单项选择题': 1,
                                '选择题': 1,
                                '判断题': 2
                            }
                            if question_type not in type_mapping:
                                raise ValueError(f"不支持的题型: {question_type}")
                            question_type_int = type_mapping[question_type]

                        # 创建Question对象
                        # 处理正确选项，确保格式标准化
                        correct_answer = row['正确选项']
                        if pd.notnull(correct_answer):
                            if isinstance(correct_answer, str):
                                # 去除首尾空格
                                correct_answer = correct_answer.strip()
                                # 确保答案是大写字母
                                correct_answer = correct_answer.upper()
                            else:
                                # 处理非字符串类型的答案（如数字等）
                                correct_answer = str(correct_answer).strip().upper()
                        
                        question = Question(
                            type=question_type_int,
                            content=row['题目'],
                            options=options,
                            correct_answer=correct_answer,
                            score=row.get('分值', 1),
                            explanation=row.get('解析', ''),
                        )
                        question.save()

                except Exception as e:
                    messages.error(request, f'导入失败: {str(e)}')
                else:
                    messages.success(request, f'成功导入{len(df)}道题目')
                return HttpResponseRedirect(reverse('admin:quiz_question_changelist'))
        
        # 增加批量删除功能的说明信息
        extra_context = extra_context or {}
        extra_context['import_form'] = QuestionImportForm()
        
        # 显示当前题目总数
        total_questions = Question.objects.count()
        extra_context['total_questions'] = total_questions
        
        return super().changelist_view(request, extra_context=extra_context)
        
class TestPaperImportForm(forms.Form):
    import_file = forms.FileField(label='Excel文件', required=True)

class TestPaperAdmin(BaseStaffAdmin):
    list_display = ('id', 'title', 'total_score', 'is_published', 'created_by', 'created_at')
    
    def changelist_view(self, request, extra_context=None):
        # 只有超级用户或有add_question权限的用户才能导入题目
        if request.user.is_superuser or request.user.has_perm('quiz.add_question'):
            if request.method == 'POST' and '_import' in request.POST:
                import_form = TestPaperImportForm(request.POST, request.FILES)
                if import_form.is_valid():
                    uploaded_file = import_form.cleaned_data['import_file']
                    try:
                        df = pd.read_excel(uploaded_file)
                        for index, row in df.iterrows():
                            # Skip empty rows
                            if row.isnull().all():
                                continue
                            # Handle question type mapping (只使用模型中定义的有效题型值)
                            question_type_mapping = {'单选题': 1, '多选题': 1, '判断题': 2}
                            question_type = row.get('类型', '单选题')
                            # 将所有非判断题映射为选择题(1)，判断题映射为2
                            question_type_int = 1  # 默认选择题
                            if question_type in question_type_mapping:
                                question_type_int = question_type_mapping[question_type]
                            elif '判断' in question_type:
                                question_type_int = 2
                            
                            # 转换选项为JSON格式
                            options = {}
                            # 检查中英文两种列名格式
                            for option_key in ['A', 'B', 'C', 'D']:
                                # 先检查中文列名（例如：选项A）
                                ch_column_name = f'选项{option_key}'
                                if ch_column_name in row and pd.notnull(row[ch_column_name]):
                                    options[option_key] = row[ch_column_name]
                                # 再检查英文列名（例如：A）
                                elif option_key in row and pd.notnull(row[option_key]):
                                    options[option_key] = row[option_key]
                                # 还可以检查其他可能的列名格式
                                elif f'Option {option_key}' in row and pd.notnull(row[f'Option {option_key}']):
                                    options[option_key] = row[f'Option {option_key}']
                                elif f'option_{option_key}' in row and pd.notnull(row[f'option_{option_key}']):
                                    options[option_key] = row[f'option_{option_key}']
                            # 处理正确选项，确保格式标准化
                            correct_answer = row.get('正确选项', '')
                            if pd.notnull(correct_answer):
                                if isinstance(correct_answer, str):
                                    # 去除首尾空格
                                    correct_answer = correct_answer.strip()
                                    # 确保答案是大写字母
                                    correct_answer = correct_answer.upper()
                                else:
                                    # 处理非字符串类型的答案（如数字等）
                                    correct_answer = str(correct_answer).strip().upper()
                            
                            question = Question(
                                type=question_type_int,
                                content=row.get('题目', ''),
                                options=options,
                                correct_answer=correct_answer,
                                score=row.get('分值', 1),
                                explanation=row.get('解析', '')
                            )
                            question.save()
                        messages.success(request, f'成功导入{len(df)}道题目')
                    except Exception as e:
                        messages.error(request, f'导入失败: {str(e)}')
                    return HttpResponseRedirect(reverse('admin:quiz_question_changelist'))
            
            extra_context = extra_context or {}
            extra_context['import_form'] = TestPaperImportForm()
        
        return super().changelist_view(request, extra_context=extra_context)
    
    list_filter = ('is_published', 'created_at')
    search_fields = ('title', 'description')
    ordering = ('-created_at',)
    filter_horizontal = ('questions',)  # 多对多关系使用水平选择器
    change_form_template = 'admin/quiz/testpaper/change_form.html'  # 使用自定义表单模板
    change_list_template = 'admin/quiz/testpaper/change_list.html'  # 使用自定义列表模板

# 注册其他模型，使用基础权限控制
class TestRecordAdmin(BaseStaffAdmin):
    list_display = ('user', 'test_paper', 'score', 'total_score', 'completed_at')
    list_filter = ('completed_at', 'test_paper')
    search_fields = ('user__username', 'test_paper__title')
    ordering = ('-completed_at',)
    # 记录类通常只用于查看，禁用编辑
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

class AnswerRecordAdmin(BaseStaffAdmin):
    list_display = ('test_record', 'question', 'user_answer', 'correct_answer', 'is_correct')
    list_filter = ('is_correct',)
    search_fields = ('question__content', 'test_record__user__username')
    # 记录类通常只用于查看，禁用编辑
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

class WrongQuestionAdmin(BaseStaffAdmin):
    list_display = ('user', 'question', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('user__username', 'question__content')
    ordering = ('-added_at',)



admin.site.register(Question, QuestionAdmin)
admin.site.register(TestPaper, TestPaperAdmin)
admin.site.register(Profile, ProfileAdmin)
admin.site.register(TestRecord, TestRecordAdmin)
admin.site.register(AnswerRecord, AnswerRecordAdmin)
admin.site.register(WrongQuestion, WrongQuestionAdmin)
