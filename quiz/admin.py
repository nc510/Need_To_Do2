from django.contrib import admin
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django import forms
from .models import Question, TestPaper, Profile
import pandas as pd
import json

class QuestionImportForm(forms.Form):
    excel_file = forms.FileField(label='Excel文件')

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'approval_status', 'created_at', 'updated_at')
    list_filter = ('approval_status', 'created_at')
    search_fields = ('user__username', 'user__email')
    ordering = ('-created_at',)

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'type', 'content', 'score', 'created_at')
    list_filter = ('type', 'created_at')
    search_fields = ('content', 'explanation')
    ordering = ('-created_at',)
    change_list_template = 'admin/quiz/question/change_list.html'
    
    # 在管理界面添加批量导入按钮和处理导入逻辑
    def changelist_view(self, request, extra_context=None):
        if request.method == 'POST' and 'excel_file' in request.FILES:
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
                        question = Question(
                            type=question_type_int,
                            content=row['题目'],
                            options=options,
                            correct_answer=row['正确选项'],
                            score=row.get('分值', 1),
                            explanation=row.get('解析', ''),
                        )
                        question.save()

                except Exception as e:
                    messages.error(request, f'导入失败: {str(e)}')
                else:
                    messages.success(request, f'成功导入{len(df)}道题目')
                return HttpResponseRedirect(reverse('admin:quiz_question_changelist'))

        # 如果不是导入请求，渲染列表页面
        extra_context = extra_context or {}
        extra_context['import_form'] = QuestionImportForm()
        return super().changelist_view(request, extra_context=extra_context)
        
class TestPaperImportForm(forms.Form):
    import_file = forms.FileField(label='Excel文件', required=True)

class TestPaperAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'total_score', 'is_published', 'created_by', 'created_at')
    
    def changelist_view(self, request, extra_context=None):
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
                        # Handle question type mapping
                        question_type_mapping = {'单选题': 1, '多选题': 2, '判断题': 3, '填空题': 4, '简答题': 5, '论述题': 6}
                        question_type = row.get('类型', '单选题')
                        question_type_int = question_type_mapping.get(question_type, 1)
                        
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
                        question = Question(
                            type=question_type_int,
                            content=row.get('题目', ''),
                            options=options,
                            correct_answer=row.get('正确选项', ''),
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



admin.site.register(Question, QuestionAdmin)
admin.site.register(TestPaper, TestPaperAdmin)
admin.site.register(Profile, ProfileAdmin)
