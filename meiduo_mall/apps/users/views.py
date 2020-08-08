import json
import logging

from django.contrib.auth.mixins import LoginRequiredMixin

from carts.utils import merge_cart_cookie_to_redis
from goods.models import SKU

logger =  logging.getLogger('django')

from django import http
from django.shortcuts import render
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from meiduo_mall.utils.view import login_required
from django.views import View
from django_redis import get_redis_connection

from users.models import User, Address
import re
from django.contrib.auth import login, authenticate, logout


# Create your views here.

#用户名验证接口
class UsernameCountView(View):
    def get(self,request,username):
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            print(e)
            return JsonResponse({
                "code": 400,
                "errmsg": "查询数据出错",
            })

        return JsonResponse({
            "code": 0,
            "errmsg": "ok",
            "count": count,
        })

#手机号验证接口
class MobileCountView(View):
    def get(self,request,mobile):

        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            print(e)
            return JsonResponse({
                "code":400,
                "errmsg":"查询数据出错",
            })

        return JsonResponse({
            "code":0,
            "errmsg":"ok",
            "count":count,


        })

#用户注册接口定义
class RegisterView(View):
    def post(self,request):
        #接收参数
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        password2 = dict.get('password2')
        mobile = dict.get('mobile')
        allow = dict.get('allow')
        sms_code_client = dict.get('sms_code')

        #整体校验
        if not all([username,password,password2,mobile,allow,sms_code_client]):
            return  http.JsonResponse({
                'code':400,
                "errmsg":"缺少必传参数"
            })

        #用户名校验
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'username格式有误'})

        #密码校验
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'password格式有误'})

        #二次输入密码校验
        if password != password2:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '两次输入不对'})

        #mobile校验
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'mobile格式有误'})

        #allow校验
        if allow != True:
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'allow格式有误'})

        #sms_code校验(链接redis数据库)
        redis_conn = get_redis_connection('sms_code')

        #从redis中取值
        sms_code_server = redis_conn.get('sms_%s' % mobile)


        #判断该值是否存在
        if not sms_code_server:
            return http.JsonResponse({
                'code':400,
                "errmsg":"短信验证码过期"
            })

        #判断验证码与发送的验证码是否一样
        if sms_code_client != sms_code_server.decode():
            return http.JsonResponse({
                'code':400,
                'errmsg':"验证码有误"
            })

        #保存到数据库捕获异常
        try:
            user = User.objects.create_user(username=username,password=password,mobile=mobile)

        except Exception as e:
            return http.JsonResponse({
                'code':400,
                'errmsg':"保存到数据库出错"
            })

        #状态保持


        login(request,user)

        #拼接json返回
        response = JsonResponse({
            'code':0,
            "errmsg":"ok"
        })

        response.set_cookie(
            'username',
            username,
            max_age=3600*24*14
        )

        return response

#用户登录接口
class LoginView(View):
    def post(self,request):
        #接受参数
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        remembered = dict.get('remembered')


        #校验
        if not all([username,password]):
            return JsonResponse({
                'code':400,
                "errmsg":'缺少必传参数'
            })
        if not re.match(r'^\w{5,20}$', username):
            return JsonResponse({'code':400, 'errmsg': '用户名格式有误'}, status=400)

        if not re.match(r'^\w{8,20}$', password):
            return JsonResponse({'code':400, 'errmsg': '密码格式有误'}, status=400)

        #验证是否能够登录
        user = authenticate(request,username=username,
                            password=password)
        if  not user:
            return JsonResponse({
                'code':400,
                'errmsg':'用户名或密码错误'

            })

        #判断是否记住密码
        if remembered:
            request.session.set_expiry(None)
        else:
            request.session.set_expiry(0)#设置为0表示关闭浏览器清除sessionid


        # try:
        #     user = User.objects.get(username=username)
        # except User.DoesNotExist as e:
        #     return JsonResponse({'code': 400, 'errmsg': '用户名错误！'})
        # if not user.check_password(password):
        #     return JsonResponse({'code': 400, 'errmsg': '密码错误！'})
        # if not user:
        #     return JsonResponse({"code": 400, 'errmsg': '您提供的身份信息无法验证！'}, status=401)
        # if remembered != True:
        #     request.session.set_expiry(0)
        #
        # else:
        #     request.session.set_expiry(None)

        # 状态保持
        login(request,user)

        #判断是否记住密码


        # #返回Json
        # return JsonResponse({
        #     'code':0,
        #     'errmsg':'ok'
        # })

        #构建响应

        response = JsonResponse({
            'code':0,
            'errmsg':"OK"
        })

        response.set_cookie(
            'username',
            username,
            max_age=3600 * 24 * 14
        )
        # 合并购物车
        response = merge_cart_cookie_to_redis(request, user, response)
        return response


#定义退出登录的接口
class LogoutView(View):

    def delete(self,request):

        #清理session
        logout(request)

        #创建response对象
        response = JsonResponse({
            'code':0,
            'errmsg':"ok"
        })
        #调用delete_cookie方法
        response.delete_cookie('username')

        #返回响应
        return response


#用户个人信息接口
class UserInfoView(View):

    #添加装饰器
    @method_decorator(login_required)
    def get(self,request):

        user = request.user

        return JsonResponse({
            'code':0,
            'errmsg':"ok",
            "info_data":{
                'username':user.username,
                'mobile': user.mobile,
                'email': user.email,
                'email_active': user.email_active
            }
        })


#导入异步模块
from celery_tasks.email.tasks import send_verify_email
#添加邮箱接口
class EmailView(View):

    @method_decorator(login_required)
    def put(self, request):
        # 1、提取参数
        data = json.loads(request.body.decode())
        email = data.get('email')
        # 2、校验参数
        if not email:
            return JsonResponse({'code': 400, 'errmsg': '缺少email'})

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({'code': 400, 'errmsg': '邮箱格式有误！'})

        # 3、数据处理(部分更新) ———— 更新邮箱
        user = request.user
        try:
            user.email = email
            user.email_active = False
            user.save()
        except Exception as e:
            print(e)


        # ======发送邮箱验证邮件=======
        verify_url = user.generate_verify_email_url()
        send_verify_email.delay(email, verify_url) # 异步调用！

        # 4、构建响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})
    # def put(self,request):
        # #接收参数
        # json_dict = json.loads(request.body.decode())
        # email = json_dict.get('email')
        #
        # #校验参数
        # if not email:
        #     return JsonResponse({
        #         'code':400,
        #         'errmsg':"缺少email参数"
        #     })
        # if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
        #     return JsonResponse({'code': 400,
        #                          'errmsg': '参数email有误'})
        #
        #
        # #赋值email字段
        # try:
        #     user.email = email
        #     user.email_active = False
        #     user.save()
        # except Exception as e:
        #     logger.error(e)
        #     print(e)
        #     return JsonResponse({
        #         'code':400,
        #         "errmsg":"添加邮箱失败"
        #     })
        #
        # #添加异步任务
        # user = request.user
        # #调用发送的函数
        # verify_url = user.generate_verify_email_url()
        # send_verify_email.delay(email,verify_url)
        #
        # return JsonResponse({
        #     'code':0,
        #     'errmsg':'ok'
        # })

#确认邮箱接口
class VerifyEmailView(View):

    """验证邮箱"""
    def put(self, request):
        # 1、提取查询字符串中token
        token = request.GET.get('token')
        # 2、校验token
        user = User.check_verify_email_token(token)
        if not user:
            return JsonResponse({'code': 400, 'errmsg': '验证邮件无效！'})

        # 3、如果token有效，把邮箱的激活状态设置为True
        user.email_active = True
        user.save()

        return JsonResponse({'code': 0, 'errmsg': '邮箱激活成功！'})

#新增地址接口
class CreateAddressView(View):

    def post(self,request):

        #获取新增地址个数：
        try:
            count = Address.objects.filter(user=request.user,is_deleted=False).count()

        except Exception as e:
            return JsonResponse({
                'code':400,
                'errmsg':'获取地址信息出错'
            })

        #判断是否超出地址上限
        if count >= 20:
            return JsonResponse({
                'code':400,
                'errmsg':'超过地址数量上限'
            })

        #接受参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        #校验参数
        if not all([receiver,province_id,city_id,district_id,place,mobile]):
            return JsonResponse({
                'code':400,
                'errmsg':'缺少必要参数'
            })

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})

        #保存地址信息
        try:
            address = Address.objects.create(
                user=request.user,
                title=receiver,
                receiver=receiver,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                place=place,
                mobile=mobile,
                tel=tel,
                email=email
            )

            #设置默认地址
            if not request.user.default_address:
                request.user.default_address = address
                request.user.save()

        except Exception as e:
            logger.error(e)
            return JsonResponse({'code': 400,
                             'errmsg': '新增地址失败'})

        # 新增地址成功，将新增的地址响应给前端实现局部刷新

        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
            }

    # 响应保存结果
        return JsonResponse({'code': 0,
                         'errmsg': '新增地址成功',
                         'address': address_dict})

#展示地址接口
class AddressView(View):
    def get(self,request):

        #获取所有地址
        addresses = Address.objects.filter(user=request.user,is_deleted=False)

        address_dict_list = []

        for address in addresses:
            address_dict = {
                "id": address.id,
                "title": address.title,
                "receiver": address.receiver,
                "province": address.province.name,
                "city": address.city.name,
                "district": address.district.name,
                "place": address.place,
                "mobile": address.mobile,
                "tel": address.tel,
                "email": address.email
            }

            #将默认地址置顶
            default_address = request.user.default_address

            if default_address.id == address.id:
                address_dict_list.insert(0,address_dict)
            else:
                address_dict_list.append(address_dict)

        default_id = request.user.default_address.id

        return JsonResponse({
            "code":0,
            "errmsg":"ok",
            "addresses":address_dict_list,
            "default_address_id":default_id
        })

#修改地址和删除地址
class UpdateDestroyAddressView(View):
    '''
    修改和删除地址接口
    '''
    def put(self,request,address_id):

        #接收参数
        json_dict = json.loads(request.body.decode())
        receiver = json_dict.get('receiver')
        province_id = json_dict.get('province_id')
        city_id = json_dict.get('city_id')
        district_id = json_dict.get('district_id')
        place = json_dict.get('place')
        mobile = json_dict.get('mobile')
        tel = json_dict.get('tel')
        email = json_dict.get('email')

        #校验参数
        if not all([address_id,receiver,province_id,city_id,district_id,place,mobile]):
            return JsonResponse({
                'code':400,
                "errmsg":'缺少校验参数'
            })
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})

        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})

        #判断地址是否存在并更新地址信息
        try:
            Address.objects.filter(id=address_id).update(
                user = request.user,
                title = receiver,
                receiver = receiver,
                province_id = province_id,
                city_id = city_id,
                district_id = district_id,
                place = place,
                mobile = mobile,
                tel = tel,
                email = email
            )
        except Exception as e:
            logger.error(e)
            return JsonResponse({
                'code':400,
                "errmsg":"更新地址失败"
            })

        #构建响应数据
        address = Address.objects.get(id=address_id)
        address_dict = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,
            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,
            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        #返回响应
        return JsonResponse({
            'code':0,
            'errmsg':"更新地址成功",
            "address":address_dict
        })

    #删除地址
    def delete(self,request,address_id):

        try:
            #查询要删除的地址
            address = Address.objects.get(id=address_id)

            #讲地址逻辑删除设置为False

            address.is_deleted = True
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({
                'code':400,
                'errmsg':"删除地址失败"
            })
        return JsonResponse({
            'code':0,
            'errmsg':"删除地址成功"
        })

# 设置默认地址接口
class DefaultAddressView(View):

    def put(self,request,address_id):
        #设置默认接口
        try:
            #接收参数
            address = Address.objects.get(id=address_id)
            request.user.default_address = address
            request.user.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({
                'code':400,
                'errmsg':'设置默认地址失败'
            })

        return JsonResponse({
            'code':0,
            'errmsg':'设置默认地址成功'
        })

#修改地址标题接口
class UpdateTitleAddressView(View):
    def put(self,request,address_id):
        #接收参数：地址标题
        json_dict = json.loads(request.body.decode())
        title = json_dict.get('title')

        try:
            #查询地址
            address = Address.objects.get(id = address_id)

            #设置新的地址标题
            address.title = title
            address.save()
        except Exception as e:
            logger.error(e)
            return JsonResponse({
                'code':400,
                'errmsg':"修改标题失败"
            })
        return JsonResponse({
            'code':0,
            'errmsg':"修改标题成功"
        })

#修改密码接口
class ChangePasswordView(LoginRequiredMixin, View):

    def put(self,request):
        #接收参数
        dict = json.loads(request.body.decode())
        old_password = dict.get('old_password')
        new_password = dict.get('new_password')
        new_password2 = dict.get('new_password2')

        #校验参数
        if not all([old_password,new_password,new_password2]):
            return JsonResponse({
                'code':400,
                'errmsg':'缺少必传参数'
            })
        result = request.user.check_password(old_password)

        #校验旧密码输入
        if not result:
            return JsonResponse({
                'code':400,
                'errmsg':'旧密码输入错误'
            })

        #校验新密码格式
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return JsonResponse({'code':400,
                                 'errmsg':'密码最少8位,最长20位'})

        #校验两次密码是否输入一致
        if new_password2 != new_password:
            return JsonResponse({
                'code':400,
                'errmsg':'两次输入密码不一致'
            })

        #修改密码
        try:
            request.user.set_password(new_password)
            request.user.save()
        except Exception as e:
            logger.error(e)

        #清理状态保持信息
        logout(request)

        response = JsonResponse({
            'code':0,
            'errmsg':'ok'
        })

        response.delete_cookie('username')

        return response

class UserBrowseHistory(View):

    #添加用户登录情况的装饰器
    @method_decorator(login_required)
    def post(self,request):
        #获取请求参数
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')

        user = request.user

        #加入用户历史浏览记录中
        conn = get_redis_connection('history')

        p = conn.pipeline()

        #lrem:如果该元素存在于集合中，那么移除这个元素
        p.lrem('history_%s'%user.id,0,sku_id)

        #左侧插入
        p.lpush('history_%s'%user.id,sku_id)

        #截断列表,只取五个元素
        p.ltrim('history_%s'%user.id,0,4)

        p.execute()

        #构建响应
        return JsonResponse({
            'code':0,
            'errmsg':'ok'
        })

    @method_decorator(login_required)
    def get(self,request):

        #展示用户浏览历史记录
        user = request.user

        conn = get_redis_connection('history')

        #1.读取redis浏览记录
        # sku_ids = [b'4', b'5', b'11']

        sku_ids = conn.lrange('history_%s'%user.id,0,-1)

        #获取sku商品信息
        # sku_ids = [int(x) for x in sku_ids]
        skus = [SKU.objects.get(id=x) for x in sku_ids]

        #构建响应
        sku_list = []
        for sku in skus:
            sku_list.append({
                'id':sku.id,
                'name':sku.name,
                'price':sku.price,
                'default_image_url':sku.default_image_url.url
            })
        return JsonResponse({
            'code':0,
            'errmsg':'ok',
            'skus':sku_list
        })



