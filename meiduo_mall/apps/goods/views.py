from django.http import JsonResponse
from django.shortcuts import render

# Create your views here.
from django.views import View
from .utils import get_breadcrumb
from django.core.paginator import Paginator, EmptyPage
#商品列表页
from goods.models import GoodsCategory, SKU


class ListView(View):

    def get(self,request,category_id):
        #获取参数
        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering =request.GET.get('ordering')

        #判断category_id 是否正确
        try:
            #获取三级菜单分类信息
            category = GoodsCategory.objects.get(id=category_id)

        except Exception as e:
            return JsonResponse({
                'code':400,
                'errmsg':"获取mysql数据出错"
            })

        #查询面包屑导航
        breadcrumb = get_breadcrumb(category)

        #排序方式
        try:
            skus = SKU.objects.filter(category=category,is_launched=True).order_by(ordering)
        except Exception as e:
            return JsonResponse({'code':400,
                                 'errmsg':'获取mysql数据出错'})

        paginator = Paginator(skus,page_size)
        #获取每页商品数据

        try:
            page_skus = paginator.page(page)
        except Exception as e:
            #如果page_num不正确，则返回错误信息
            return JsonResponse({
                'code':400,
                'errmsg':'page数据出错'
            })

        #获取列表页总页数
        total_page = paginator.num_pages

        #定义列表
        list = []
        #整理格式
        for sku in page_skus:
            list.append({
                'id':sku.id,
                'default_image_url':sku.default_image_url.url,
                'name':sku.name,
                'price':sku.price
            })

        #返回响应
        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'breadcrumb':breadcrumb,
            "list":list,
            'count':total_page

        })

#商品热销排行
class HotGoodsView(View):
    def get(self,request,category_id):
        #根据销量排行
        try:
            skus = SKU.objects.filter(category_id=category_id,is_launched=True).order_by('-sales')[:3]
        except Exception as e:
            return JsonResponse({
                'code':400,
                'errmsg':'获取商品出错'
            })

        #转换格式
        hot_skus = []

        for sku in skus:
            hot_skus.append({
                "id":sku.id,
                'default_image_url':sku.default_image_url.url,
                'name':sku.name,
                "price":sku.price
            })

        return JsonResponse({
            'code':0,
            'errmsg':'OK',
            'hot_skus':hot_skus
        })

    # 导入:
from haystack.views import SearchView

#商品搜索视图
class MySearchView(SearchView):
    #重写SearchView类
    # def create_response(self):
    #     context = self.get_context()
    #     # page = self.request.GET.get('page')
    #     #获取搜索结果
    #
    #     data_list = []
    #     for sku in context['page'].object_list:
    #         data_list.append({
    #             'id':sku.object.id,
    #             'name':sku.object.name,
    #             'price':sku.object.price,
    #             'default_image_url':sku.object.default_image_url.url,
    #             'searchkey':context['query'],
    #             'page_size':context['paginator'].per_page,
    #             'count':context['paginator'].count
    #         })
    #
    #     return JsonResponse(data_list,safe=False)
    # 构建一个响应
    def create_response(self):
        # 默认SearchView搜索视图逻辑：先搜索出结果，再调用create_response函数构建响应

        # 1、获取全文检索的结果
        context = self.get_context()

        # context['query'] 检索词
        # context['paginator'] 分页器对象
        # context['paginator'].count 数据量
        # context['paginator'].num_pages 当前页
        # context['page'].object_list 列表(SearchResult对象)
        # SearchResult.object 被搜索到的SKU模型类对象

        sku_list = []
        # 2、从查询的结果context中提取查询到的sku商品数据
        for search_result in context['page'].object_list:
            # search_result: SearchResult对象
            # search_result.object: SKU模型类对象
            sku = search_result.object
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image_url.url,
                'searchkey': context['query'],
                'page_size': context['paginator'].per_page,
                'count': context['paginator'].count
            })


        # sku_list = [
        #     {
        #         'id': 1,
        #         'name': '苹果100',
        #         'price': 10,
        #         'default_image_url': 'http://image.meiduo.site:8888/group1/M00/00/02/CtM3BVrPB4GAWkTlAAGuN6wB9fU4220429',
        #         'searchkey': '华为',
        #         'page_size': 5,
        #         'count': 12
        #     }
        # ]

        return JsonResponse(sku_list, safe=False)
