

# 将我们之前写的获取商品分类的代码,提取出来一部分, 封装成一个独立的函数:

# 导入:
from copy import deepcopy

from django import http
from collections import OrderedDict
from goods.models import GoodsCategory, SPUSpecification
from goods.models import GoodsChannel, SKU
from goods.models import SKUImage, SKUSpecification
from goods.models import SpecificationOption


def get_breadcrumb(category):

    # 定义一个字典:
    dict = {
        'cat1':'',
        'cat2':'',
        'cat3':''
    }
    # 判断 category 是哪一个级别的.
    # 注意: 这里的 category 是 GoodsCategory对象
    if category.parent is None:
        # 当前类别为一级类别
        dict['cat1'] = category.name
    # 因为当前这个表示自关联表, 所以关联的对象还是自己:
    elif category.parent.parent is None:
        # 当前类别为二级
        dict['cat2'] = category.name
        dict['cat1'] = category.parent.name
    else:
        # 当前类别为三级
        dict['cat3'] = category.name
        dict['cat2'] = category.parent.name
        dict['cat1'] = category.parent.parent.name

    return dict

def get_goods_and_spec(sku_id):

    #根据sku_id获取该商品
    sku = SKU.objects.get(id = sku_id)
    #获取该商品的图片
    sku.default_image_url = sku.default_image_url.url
    #记录当前sku的选项组合
    cur_sku_spec_options =SKUSpecification.objects.filter(sku=sku).order_by('spec_id')

    cur_sku_options = [] # [1,4,7]

    for temp in cur_sku_spec_options:
        # temp是SKUSpecification中间表对象
        cur_sku_options.append(temp.option_id)

        # spu对象(SPU商品)
    goods = sku.spu
    # 罗列出和当前sku同类的所有商品的选项和商品id的映射关系
    # {(1,4,7):1, (1,3,7):2}
    sku_options_mapping = {}
    skus = SKU.objects.filter(spu=goods)
    for temp_sku in skus:
        # temp_sku:每一个sku商品对象
        sku_spec_options = SKUSpecification.objects.filter(sku=temp_sku).order_by('spec_id')
        sku_options = []
        for temp in sku_spec_options:
            sku_options.append(temp.option_id)  # [1,4,7]
        sku_options_mapping[tuple(sku_options)] = temp_sku.id  # {(1,4,7):1}

    # specs当前页面需要渲染的所有规格
    specs = SPUSpecification.objects.filter(spu=goods).order_by('id')
    for index, spec in enumerate(specs):
        # spec每一个规格对象
        options = SpecificationOption.objects.filter(spec=spec)

        # 每一次选项规格的时候，准备一个当前sku的选项组合列表，便于后续使用
        temp_list = deepcopy(cur_sku_options)  # [1,4,7]

        for option in options:
            # 每一个选项，动态添加一个sku_id值，来确定这个选项是否属于当前sku商品

            temp_list[index] = option.id  # [1,3,7] --> sku_id?

            option.sku_id = sku_options_mapping.get(tuple(temp_list))  # 找到对应选项组合的sku_id

        # 在每一个规格对象中动态添加一个属性spec_options来记录当前规格有哪些选项
        spec.spec_options = options

    return goods, sku, specs


def get_categories():
    #模板参数categories是首页分类频道
    categories = {}

    #获取首页所有的分类频道数据
    channels = GoodsChannel.objects.order_by("group_id",'sequence')
    #遍历所有的分类频道，构建以组号作为key的键值对
    for channel in channels:
        # channel: GoodsChannel对象
        if channel.group_id not in categories:
            categories[channel.group_id] = {
                'channels':[],
                'sub_cats':[]
            }
        #填充一级分类
        cat1 = channel.category
        categories[channel.group_id]['channels'].append({
            'id':cat1.id,
            'name':cat1.name,
            'url':channel.url
        })

        # (2)、填充当前组中的二级分类
        cat2s = GoodsCategory.objects.filter(parent=cat1)
        for cat2 in cat2s:
            # cat2：二级分类对象

            cat3_list = []  # 每一次遍历到一个二级分类对象的时候，初始化一个空列表，用来构建三级分类
            cat3s = GoodsCategory.objects.filter(parent=cat2)
            # (3)、填充当前组中的三级分类
            for cat3 in cat3s:
                # cat3；三级分类对象
                cat3_list.append({
                    'id': cat3.id,
                    'name': cat3.name
                })

            categories[channel.group_id]['sub_cats'].append({
                'id': cat2.id,
                'name': cat2.name,
                'sub_cats': cat3_list  # 三级分类
            })

    return categories

