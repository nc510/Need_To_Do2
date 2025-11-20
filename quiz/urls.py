from django.urls import path
from . import views

urlpatterns = [
    path('test_paper_list/', views.test_paper_list, name='test_paper_list'),  # 试卷列表
    
    path('question/<int:question_id>/', views.question_detail, name='question_detail'),
    path('paper/<int:paper_id>/', views.test_paper_detail, name='test_paper_detail'),  # 试卷详情
    path('paper/<int:paper_id>/submit/', views.submit_test_paper, name='submit_test_paper'),  # 试卷提交
    
    path('register/', views.register, name='register'),  # 注册
    path('login/', views.login_view, name='login'),  # 登录
    path('logout/', views.logout_view, name='logout'),  # 退出登录
    path('test_history/', views.test_history, name='test_history'),  # 答题历史
    path('test_history/<int:record_id>/', views.test_history_detail, name='test_history_detail'),  # 答题历史详情
    path('user_center/', views.user_center, name='user_center'),  # 用户中心
    path('wrong_question_notebook/', views.wrong_question_notebook, name='wrong_question_notebook'),  # 错题本
    path('create_wrong_question_paper/', views.create_wrong_question_paper, name='create_wrong_question_paper'),  # 错题本组卷
    path('submit_wrong_question_paper/', views.submit_wrong_question_paper, name='submit_wrong_question_paper'),  # 错题本试卷提交
    path('delete_wrong_question/<int:wrong_question_id>/', views.delete_wrong_question, name='delete_wrong_question'),  # 删除错题
]