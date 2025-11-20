from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models.signals import m2m_changed
from django.dispatch import receiver

class Question(models.Model):
    # 题目类型：1-选择题，2-判断题
    TYPE_CHOICE = (1, '选择题'), (2, '判断题')
    type = models.IntegerField(choices=TYPE_CHOICE, verbose_name='题目类型')
    content = models.TextField(verbose_name='题目内容')
    options = models.JSONField(verbose_name='选项', default=dict, blank=True, help_text='选择题选项，格式：{"A":"选项内容","B":"选项内容"}')
    correct_answer = models.CharField(max_length=10, verbose_name='正确答案')
    score = models.IntegerField(verbose_name='分值', default=1)
    explanation = models.TextField(verbose_name='解析', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '题目'
        verbose_name_plural = '题目'
        ordering = ['-created_at']

    def __str__(self):
        return self.content

class TestPaper(models.Model):
    title = models.CharField(max_length=100, verbose_name='试卷标题')
    description = models.TextField(verbose_name='试卷描述', null=True, blank=True)
    questions = models.ManyToManyField(Question, verbose_name='包含题目')
    total_score = models.IntegerField(verbose_name='总分', default=0)
    created_by = models.CharField(max_length=50, verbose_name='出题人', default='admin')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    is_published = models.BooleanField(verbose_name='是否发布', default=False)

    class Meta:
        verbose_name = '试卷'
        verbose_name_plural = '试卷'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # 只有已存在的实例才计算总分（避免新建时访问多对多关系）
        if self.pk:
            self.total_score = sum(question.score for question in self.questions.all())
        super().save(*args, **kwargs)

# 使用信号监听ManyToMany关系变化，确保添加/移除题目时更新总分
@receiver(m2m_changed, sender=TestPaper.questions.through)
def update_testpaper_total_score(sender, instance, action, **kwargs):
    # 只有在题目添加、移除或清空后才更新总分
    if action in ['post_add', 'post_remove', 'post_clear']:
        instance.total_score = sum(question.score for question in instance.questions.all())
        instance.save()

class Profile(models.Model):
    # 与User模型一对一关联
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name='用户')
    # 审核状态：0-未审核，1-审核通过，2-审核拒绝
    APPROVAL_STATUS = (0, '未审核'), (1, '审核通过'), (2, '审核拒绝')
    approval_status = models.IntegerField(choices=APPROVAL_STATUS, default=0, verbose_name='审核状态')
    phone_number = models.CharField(max_length=11, verbose_name='手机号码', blank=True, null=True, unique=True)
    qq_number = models.CharField(max_length=20, verbose_name='QQ号码', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '会员信息'
        verbose_name_plural = '会员信息'

    def __str__(self):
        return self.user.username

# 创建User时自动创建Profile
@receiver(post_save, sender=User)
def ensure_profile_exists(sender, instance, **kwargs):
    try:
        instance.profile
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)

# 保存User时自动保存Profile
@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()

class TestRecord(models.Model):
    # 答题记录
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    test_paper = models.ForeignKey(TestPaper, on_delete=models.CASCADE, verbose_name='试卷')
    score = models.IntegerField(verbose_name='得分')
    total_score = models.IntegerField(verbose_name='总分')
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name='完成时间')

    class Meta:
        verbose_name = '答题记录'
        verbose_name_plural = '答题记录'
        ordering = ['-completed_at']

    def __str__(self):
        return f'{self.user.username} - {self.test_paper.title} - {self.score}/{self.total_score}'

class AnswerRecord(models.Model):
    # 每题答题记录
    test_record = models.ForeignKey(TestRecord, on_delete=models.CASCADE, verbose_name='答题记录')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='题目')
    user_answer = models.CharField(max_length=10, verbose_name='用户答案', null=True, blank=True)
    correct_answer = models.CharField(max_length=10, verbose_name='正确答案')
    is_correct = models.BooleanField(verbose_name='是否正确')
    
    # 原始题目信息（保留答题时的题目内容）
    original_question_content = models.TextField(verbose_name='原始题目内容', null=True, blank=True)
    original_question_type = models.IntegerField(verbose_name='原始题目类型', choices=Question.TYPE_CHOICE, null=True, blank=True)
    original_options = models.JSONField(verbose_name='原始选项', default=dict, blank=True, help_text='原始选择题选项，格式：{"A":"选项内容","B":"选项内容"}')
    original_explanation = models.TextField(verbose_name='原始解析', null=True, blank=True)

    class Meta:
        verbose_name = '每题答题记录'
        verbose_name_plural = '每题答题记录'

class WrongQuestion(models.Model):
    # 错题本
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='用户')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='题目')
    user_answer = models.CharField(max_length=10, verbose_name='用户错误答案', null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')

    class Meta:
        verbose_name = '错题本'
        verbose_name_plural = '错题本'
        # 一个用户一个题目只能出现一次
        unique_together = ('user', 'question')

    def __str__(self):
        return f'{self.user.username} - {self.question.content}'
