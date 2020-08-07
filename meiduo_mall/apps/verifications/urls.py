from django.contrib import admin
from django.urls import path,re_path,include

from . import views

urlpatterns = [
    #添加verifications的总路由
    re_path(r"^image_codes/(?P<uuid>[\w-]+)/$",views.ImageCodeView.as_view()),
    re_path(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$',views.SMSCodeView.as_view()),
]
