from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View
from goods.models import GoodsSKU
from django_redis import get_redis_connection
from utils.mixin import LoginRequiredMixin


class CartAddView(View):
    '''购物车记录添加'''
    def post(self, request):
        # 判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')

        # 校验数据
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        try:
            count = int(count)
        except Exception as e:
            # 商品数目出错
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理： 添加购物车记录
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        # 先尝试获取cart_key中的sku_id的值
        sku_count = conn.hget(cart_key, sku_id)

        if sku_count:
            # 如果商品信息已经在缓存中需要累加
            count += int(sku_count)

        # 校验商品的库存，商品数不能超过库存数
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '库存不足'})

        # 添加记录
        conn.hset(cart_key, sku_id, count)

        # 获取用户购物车中的数量
        cart_count = conn.hlen(cart_key)

        # 返回应答
        return JsonResponse({'res':5, 'cart_count': cart_count, 'message': '添加成功'})


# '/cart/'
class CartInfoView(LoginRequiredMixin, View):
    ''' 在购物车中显示'''
    def get(self, request):
        # 获取当前登录的用户信息
        user = request.user
        # 获取用户购物车中的信息
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        cart_dict = conn.hgetall(cart_key)

        skus = []
        # 分别保存用户购物车中的总数和总价格
        total_count = 0
        total_price = 0
        for sku_id, count in cart_dict.items():
            # 根据sku_id获取商品的信息
            sku = GoodsSKU.objects.get(id=sku_id)
            # 计算商品的小计
            amount = sku.price * int(count)
            # 动态给sku增加一个属性amount，保存商品的小计
            sku.amount = amount
            # 动态给sku增加一个属性count，保存商品的数量
            sku.count = count

            skus.append(sku)
            # 累计计算商品的总件数和总价格
            total_count += int(count)
            total_price += amount

        # 组织上下文
        context = {
            'skus':skus,
            'total_count': total_count,
            'total_price': total_price
        }

        # 返回模板
        return render(request, 'cart.html', context)


# 更新购物车记录
# 前端发起ajax post请求
# 前端需要传递的参数有，商品id 商品count
# 更新购物车中的记录
class CartUpdateView(View):
    '''购物车记录更新'''
    def post(self, request):
        # 判断用户是否已经登录
        user = request.user
        # 用户没有登录
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg':'请先登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        count = request.POST.get('count')
        #进行校验
        if not all([sku_id, count]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 校验商品数目
        try:
            count = int(count)
        except Exception as e:
            # 商品数目出错
            return JsonResponse({'res': 2, 'errmsg': '商品数目出错'})

        # 校验商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 3, 'errmsg': '商品不存在'})

        # 业务处理： 购物车商品处理
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        # 校验商品的库存
        if count > sku.stock:
            return JsonResponse({'res': 4, 'errmsg': '商品库存不足'})

        # 更新购物车
        conn.hset(cart_key, sku_id, count)

        # 获取购物车中全部商品的总数
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        # 返回应答
        return JsonResponse({'res':5, 'message': '添加成功'})


# 购物车中记录删除
# 采用ajax post请求
# 前端传来的数据有 商品的id
#　/cart/delete
class CartDeletView(View):
    def post(self, request):
        # 判断用户是否已经登录
        user = request.user
        # 如果用户没有登录
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 接收数据
        sku_id = request.POST.get('sku_id')
        # 数据校验
        # 若传来的数据不完整
        if not sku_id:
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 判断商品是否存在
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return JsonResponse({'res': 2, 'errmsg': '商品不存在'})

        # 获取购物车内容
        conn = get_redis_connection('default')
        # 删除购物车记录
        cart_key = 'cart_%d' % user.id
        conn.hdel(cart_key, sku_id)

        # 获取购物车中的商品条目数
        total_count = 0
        vals = conn.hvals(cart_key)
        for val in vals:
            total_count += int(val)

        return JsonResponse({'res': 3, 'message': '删除成功'})