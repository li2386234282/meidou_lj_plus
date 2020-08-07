
from django.contrib import admin
from django.urls import path,re_path

from users import views

urlpatterns = [
    #用户名检验路由
    re_path(r'^usernames/(?P<username>\w{5,20})/count/$',views.UsernameCountView.as_view()),
    #手机号校验路由
    re_path(r"^mobiles/(?P<mobile>1[3-9]\d{9})/count/$",views.MobileCountView.as_view()),
    #用户注册路由
    re_path(r"^register/$",views.RegisterView.as_view()),
    #登录
    re_path(r"^login/$",views.LoginView.as_view()),
    #登出
    re_path(r"^logout/$", views.LogoutView.as_view()),
    #用户中心路由
    re_path(r'^info/$', views.UserInfoView.as_view()),
    #更新邮箱
    re_path(r'^emails/$', views.EmailView.as_view()),
    # 发送邮箱验证码的路由
    re_path(r'^emails/verification/$', views.VerifyEmailView.as_view()),
    #创建收货地址的路由
    re_path(r'^addresses/create/$', views.CreateAddressView.as_view()),
    # 展示地址的子路由:
    re_path(r'^addresses/$', views.AddressView.as_view()),
    #添加和删除收货地址
    re_path(r'^addresses/(?P<address_id>\d+)/$', views.UpdateDestroyAddressView.as_view()),
    # 设置默认地址
    re_path(r'^addresses/(?P<address_id>\d+)/default/$', views.DefaultAddressView.as_view()),
    # 更新地址标题
    re_path(r'^addresses/(?P<address_id>\d+)/title/$', views.UpdateTitleAddressView.as_view()),
    # 修改密码
    re_path(r'^password/$', views.ChangePasswordView.as_view()),
    # 用户浏览记录
    re_path(r'^browse_histories/$', views.UserBrowseHistory.as_view()),

]