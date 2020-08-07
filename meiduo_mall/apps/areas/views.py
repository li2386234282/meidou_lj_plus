
# Create your views here.
from django.http import JsonResponse
from django.views import View
from django.core.cache import cache

from areas.models import Area
from django import http

class ProvinceAreasView(View):
    """提供省级地区数据
            1.查询省级数据
            2.序列化省级数据
            3.响应省级数据
            4.补充缓存逻辑
            """
    def get(self, request):
        try:
            #查询省级数据
            province_model_list = Area.objects.filter(parent__isnull=True)

            province_list = []

            #整理数据
            for province_model in province_model_list:
                province_list.append({'id':province_model.id,
                                      'name':province_model.name})

                # 增加: 缓存省级数据
                cache.set('province_list', province_list, 3600)
        except Exception as e:
            return JsonResponse({
                'code':400,
                "errmsg":"省份数据错误"
            })

        return JsonResponse({
            'code':0,
            'errmsg':"ok",
            'province_list':province_list
})

class SubAreasView(View):
    """子级地区：市和区县"""

    def get(self, request, pk):
        """提供市或区地区数据
        1.查询市或区数据
        2.序列化市或区数据
        3.响应市或区数据
        4.补充缓存数据
        """
        try:
            #查询市或区数据
            sub_model_list = Area.objects.filter(parent=pk)

            #查询省份数据
            parent_model = Area.objects.get(id=pk)

            sub_list = []
            for sub_model in sub_model_list:
                sub_list.append({"id":sub_model.id,
                                 "name":sub_model.name})

                sub_data = {
                    'id':parent_model.id,
                    'name':parent_model.name,
                    'subs':sub_list
                }
                # 缓存市或区数据
                cache.set('sub_area_%s' %pk, sub_data, 3600)
        except Exception as e:
            return JsonResponse({
                'code':400,
                'errmsg':"城市或区县数据错误"
            })

        return JsonResponse({
            'code':0,
            'errmsg':"ok",
            'sub_data':sub_data,
        })