from django.shortcuts import render, redirect
from django.views.generic import View
from goods.models import GoodsSKU
from order.models import OrderInfo, OrderGoods
from django_redis import get_redis_connection
from django.core.urlresolvers import reverse
from utils.mixin import LoginRequiredMixin
from django.http import JsonResponse
from user.models import Address
from datetime import datetime

# dCreate your views here.
# 订单页面


class OrderPlaceView(LoginRequiredMixin, View):
    def post(self, request):
        # 获取登录的用户
        user = request.user
        # 接收数据
        sku_ids = request.POST.getlist('sku_ids')
        # print(sku_ids)
        # 进行校验
        # 如果购物车中商品为空
        if not sku_ids:
            return redirect(reverse('cart:cart'))

        # 业务处理获取用户地址信息
        addrs = Address.objects.filter(user=user)

        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id

        # 保存商品的总件数和总金额
        total_count = 0
        total_price = 0
        # 保存商品的信息
        skus = []
        for sku_id in sku_ids:
            # 将前端传来的商品的id遍历，得到每一个商品id
            sku = GoodsSKU.objects.get(id=sku_id)
            # 获取用户购买商品的数目
            count = conn.hget(cart_key, sku_id)
            # 计算商品的小计
            amount = sku.price * int(count)
            # 动态的给sku给一个属性，保存商品的小计
            sku.amount = amount
            # 动态给sku一个属性，保存商品的数目
            sku.count = count
            # 添加到商品表中
            skus.append(sku)
            # 商品的总数
            total_count += int(count)
            # 商品的总价
            total_price += amount

        # 运费
        transit_price = 10

        # 实际付款
        total_pay = total_price + transit_price

        # 组织上下文
        sku_ids = ','.join(sku_ids)
        context = {
            'skus': skus,
            'addrs': addrs,
            'total_price': total_price,
            'total_count': total_count,
            'transit_price': transit_price,
            'total_pay': total_pay,
            'sku_ids': sku_ids
        }

        return render(request, 'place_order.html',context)


# 订单提交
# 采用ajax post 请求
# 前端发来的商品id, 用户的地址， 和支付方式
class OrderCommitView(View):
    def post(self, request):
        # 首先判断用户是否登录
        user = request.user
        if not user.is_authenticated():
            return JsonResponse({'res': 0, 'errmsg': '请先登录'})

        # 获取发来的商品id
        sku_ids = request.POST.get('sku_ids')
        # 获取发来的用户的地址id
        addr_id = request.POST.get('add_id')
        # 获取支付方式
        pay_method = request.POST.get('pay_method')

        # 数据校验
        if not all([sku_ids, addr_id, pay_method]):
            return JsonResponse({'res': 1, 'errmsg': '数据不完整'})

        # 验证支付方式
        if pay_method not in OrderInfo.PAY_METHODS.keys():
            return JsonResponse({'res': 2, 'errmsg': '支付方式不存在'})

        # 校验地址
        try:
            addr = Address.objects.get(id=addr_id)
        except Address.DoesNotExist:
            # 地址不存在
            return JsonResponse({'res': 3, 'errmsg': '地址信息错误'})

        # 业务处理
        # 组织订单数据
        # 订单id， 格式：20171122211120 + 用户id
        order_id = datetime.now().strftime('%Y%m%d%H%M%S') + str(user.id)

        # 运费
        transit_price = 10

        # 总金额和总数
        total_count = 0
        total_price = 0

        # 向订单表中添加一条记录
        order = OrderInfo.objects.create(order_id=order_id,
                                         user=user,
                                         addr=addr,
                                         pay_method=pay_method,
                                         total_count=total_count,
                                         total_price=total_price,
                                         transit_price=transit_price,
                                         )

        # 向订单商品表中添加记录时，用户买了几件商品，需要添加几件商品
        conn = get_redis_connection('default')
        cart_key = 'cart_%d' % user.id
        sku_ids = sku_ids.split(',')

        # 遍历获得订单中商品的id
        for sku_id in sku_ids:
            # 根据商品id获得商品的信息，
            try:
                sku = GoodsSKU.objects.get(id=sku_id)
            except GoodsSKU.DoesNotExist:
                return JsonResponse({'res':4, 'errmsg': '该商品不存在'})

            # 获取用户购物车商品的数量
            count = conn.hget(cart_key, sku_id)

            # 向订单商品中添加一条商品的信息
            OrderGoods.objects.create(order=order,
                                      sku=sku,
                                      count=count,
                                      price=sku.price)

            # 更新对应商品的库存和销量
            sku.stock -= int(count)
            sku.sales += int(count)
            sku.save()

            # 累加计算订单中的商品的总数和总价
            total_count += int(count)
            amount = sku.price * int(count)
            total_price += amount

        # 更新订单表中订单的总价和总数
        order.total_count = total_count
        order.total_price = total_price
        order.save()

        # 删除用户购物车中对应的购物车记录
        # 因为sku_ids 是列表，
        conn.hdel(cart_key, *sku_ids)

        # 返回应答
        return JsonResponse({'res': 5, 'message': '订单创建成功'})
