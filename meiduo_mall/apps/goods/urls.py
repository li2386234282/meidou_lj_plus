from django.urls import path,re_path,include

import users
from goods import views

urlpatterns = [
    #商品列表页
    re_path(r'^list/(?P<category_id>\d+)/skus/$', views.ListView.as_view()),
    # 热销商品排行
    re_path(r'^hot/(?P<category_id>\d+)/$', views.HotGoodsView.as_view()),
    #商品搜索路由
    re_path(r'^search/$', views.MySearchView()),
]