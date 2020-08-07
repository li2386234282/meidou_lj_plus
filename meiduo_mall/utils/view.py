from django.http import JsonResponse


def  login_required(func):
    #自定义的装饰器
    def wrapper(request,*args,**kwargs):
        if request.user.is_authenticated:
            #如果用户登录，则执行下面的语句
            return func(request,*args,**kwargs)
        else:
            #如果用户未登录，则返回如下的代码
            return JsonResponse({
                'code':400,
                'errmsg':"请登录后重试"
            })
    return wrapper



