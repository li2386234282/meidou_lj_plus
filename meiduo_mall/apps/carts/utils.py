from django_redis import get_redis_connection
import pickle,base64


#cookie数据的编码
def carts_cookie_encode(cart_dict):
    return base64.b64encode(
        pickle.dumps(cart_dict)
                ).decode()

#cookie数据的解码
def carts_cookie_decode(cart_str):
    return pickle.loads(
        base64.b64decode(cart_str.encode())
    )



def merge_cart_cookie_to_redis(request,user,response):
    """
    登录后合并cookie购物车数据到Redis
    :param request: 本次请求对象，获取 cookie 中的数据
    :param response: 本次响应对象，清除 cookie 中的数据
    :param user: 登录用户信息，获取 user_id
    :return: response
    """
    #获取cookie中的redis数据
    cart_dict = {}  # 初始化孔子点，保存cookie购物数据
    cookie_str = request.COOKIES.get('carts')

    #cookie中没有数据就响应结果
    if  cookie_str:
        cart_dict = carts_cookie_decode(cookie_str)

    #合并到redis中
    # (1)、sku_id和count添加到redis中
    new_add = cart_dict.keys() # 记录所有需要添加到redis中的sku_id


    conn = get_redis_connection('carts')

    for sku_id in new_add:
        conn.hmset('carts_%s'%user.id,{sku_id:cart_dict[sku_id]['count']})
    #将勾选状态同步到数据库
        if cart_dict[sku_id]['selected']:
            conn.sadd('selected_%s'%user.id,sku_id)

        else:
            conn.srem('selected_%s'%user.id,sku_id)

    #清楚cookie
    response.delete_cookie('carts')

    return response




