"""
WSGI config for need_to_do project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/wsgi/
"""

import os
from whitenoise import WhiteNoise

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'need_to_do.settings')

# 获取Django应用
application = get_wsgi_application()
# 使用WhiteNoise包装应用以提供静态文件服务
application = WhiteNoise(application)
# 确保静态文件目录被正确配置
from django.conf import settings
application.add_files(settings.STATIC_ROOT, prefix='static/')
