import random
import re

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

# Create your views here.
# from meiduo_mall.libs.captcha.captcha import captcha
#
# text,image = captcha.generate_captcha()
from django import http
from django.views.generic.base import View
from django_redis import get_redis_connection

from meiduo_mall.libs.captcha.captcha import captcha
import logging
from celery_tasks.sms.tasks import ccp_send_sms_code

from meiduo_mall.libs.yuntongxun.ccp_sms import CCP

logger = logging.getLogger('django')

class ImageCodeView(View):
    def get(self,request,uuid):


        text,image =captcha.generate_captcha()

        redis_conn = get_redis_connection("verify_code")

        redis_conn.setex('img_%s'%uuid,300,text)

        return HttpResponse(
            image,content_type="image/jpg"
        )


class SMSCodeView(View):
    def get(self,request,mobile):


        # 1、提取参数
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')

        # 2、校验参数
        if not all([image_code, uuid]):
            return JsonResponse({
                'code': 400,
                'errmsg': '缺少必要参数'
            }, status=400)
        if not re.match(r'^\w{4}$', image_code):
            return JsonResponse({
                'code': 400,
                'errmsg': '图片验证码格式不符'
            }, status=400)
        if not re.match(r'^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$', uuid):
            return JsonResponse({
                'code': 400,
                'errmsg': 'uuid格式不符'
            }, status=400)

        # 3、校验redis中的图片验证码是否一致——业务层面上的校验
        conn = get_redis_connection('verify_code')
        # 3.1 提取redis中存储的图片验证码
        # get(): b"YBCF"
        image_code_from_redis = conn.get("img_%s"%uuid)

        # 如果从redis中读出的验证码是空；
        if not image_code_from_redis:
            return JsonResponse({'code':400, 'errmsg': '验证码过期'}, status=400)
        # 如果读出来的不是空，我们要删除该验证码
        image_code_from_redis = image_code_from_redis.decode()
        conn.delete("img_%s"%uuid)

        # 3.2 比对（忽略大小写）
        if image_code.lower() != image_code_from_redis.lower():
            return JsonResponse({
                'code': 400,
                'errmsg': '图形验证码输入错误'
            }, status=400)


        # 4、发送短信验证码
        conn = get_redis_connection('sms_code')
        # 判断60秒之内，是否发送过短信——判断标志信息是否存在
        flag = conn.get('flag_%s'%mobile)
        if flag:
            return JsonResponse({'code':400, 'errmsg':'请勿重复发送短信'}, status=400)
        #随机生成六位数验证码
        sms_code = '%06d'%random.randint(0,999999)
        logger.info(sms_code)
        print("手机验证码",sms_code)

        #创建管道
        pl = conn.pipeline()

        # 按顺序执行
        # redis_conn.setex('sms_%s' % mobile, 300, sms_code)
        pl.setex('sms_%s' % mobile, 300, sms_code)

        # redis_conn.setex('send_flag_%s' % mobile, 60, 1)
        pl.setex('send_flag_%s' % mobile, 60, 1)

        #执行管道
        pl.execute()


        # CCP().send_template_sms(mobile,[sms_code,5],1)

        ccp_send_sms_code.delay(mobile,sms_code)

        #响应结果
        return http.JsonResponse({
            'code':0,
            'errmsg':"发送短信成功"
        })





