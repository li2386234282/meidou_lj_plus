from django import urls
from django.urls import re_path
from areas import views

urlpatterns = [
    #省级地区
    re_path(r'^areas/$', views.ProvinceAreasView.as_view()),
    #子级地区
    re_path(r'^areas/(?P<pk>[1-9]\d+)/$', views.SubAreasView.as_view()),
]