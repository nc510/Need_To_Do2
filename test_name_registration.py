import os
import django

# 先初始化Django设置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'need_to_do.settings')
django.setup()

# 然后再导入其他模块
from django.test import Client
from django.urls import reverse
from django.contrib.auth.models import User
from quiz.models import Profile

# 使用简单函数测试，不使用TestCase类
def test_registration_with_name():
    # 确保测试前没有相同用户名的用户
    User.objects.filter(username='testuser').delete()
    
    # 创建测试客户端
    client = Client()
    
    # 准备测试数据
    test_data = {
        'username': 'testuser',
        'password': 'testpassword123',
        'password_confirm': 'testpassword123',
        'email': 'testuser@example.com',
        'name': '测试用户',
        'phone_number': '13800138000',
        'qq_number': '123456789'
    }
    
    # 发送POST请求到注册视图
    response = client.post(reverse('register'), test_data)
    
    # 验证用户是否创建成功
    user_exists = User.objects.filter(username='testuser').exists()
    print(f'用户创建状态: {user_exists}')
    
    if user_exists:
        # 获取创建的用户和对应的Profile
        user = User.objects.get(username='testuser')
        profile = Profile.objects.get(user=user)
        
        # 验证姓名是否正确保存
        name_saved = profile.name == '测试用户'
        print(f'姓名保存状态: {name_saved}')
        print(f'保存的姓名: {profile.name}')
        
        if name_saved:
            print('测试通过！注册功能中的姓名字段已正确保存到数据库。')
            return True
        else:
            print('测试失败！姓名未正确保存。')
            return False
    else:
        print('测试失败！用户未创建成功。')
        return False

if __name__ == '__main__':
    # 运行测试
    success = test_registration_with_name()
    if success:
        print('所有测试完成，姓名字段功能正常！')
    else:
        print('测试失败，请检查代码。')