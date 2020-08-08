
from django.contrib import admin
from django.urls import path,re_path,include

import users
from carts import views

urlpatterns = [
    # 购物车查询和新增和修改和删除
    re_path(r'^carts/$', views.CartsView.as_view()),
    # 购物车全选
    re_path(r'^carts/selection/$', views.CartSelectAllView.as_view()),

# 提供商品页面右上角购物车数据
    re_path(r'^carts/simple/$', views.CartsSimpleView.as_view()),
]