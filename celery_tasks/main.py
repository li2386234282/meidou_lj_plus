# 在异步任务程序中加载django的环境
import os
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'meiduo_mall.settings.dev'
)

from celery import Celery


celery_app = Celery('meiduo_mall_task')


# 里面的参数为我们创建的 config 配置文件:
celery_app.config_from_object('celery_tasks.config')

celery_app.autodiscover_tasks(['celery_tasks.sms',
                               'celery_tasks.email',
                               'celery_tasks.html'
                               ])
