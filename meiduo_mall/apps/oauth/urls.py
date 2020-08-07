from django.urls import re_path

from oauth import views

urlpatterns = [
    # 获取 QQ 扫码登录链接
    re_path(r'^qq/authorization/$', views.QQFirstView.as_view()),
    re_path(r'^oauth_callback/$', views.QQUserView.as_view()),

]

