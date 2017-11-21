from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
from django.views.generic import View
from django.core.cache import cache
from utils.mixin import LoginRequiredMixin
from django_redis import get_redis_connection
from goods.models import GoodsType, GoodsSKU, IndexGoodsBanner, IndexPromotionBanner, IndexTypeGoodsBanner
from order.models import OrderGoods


class IndexView(LoginRequiredMixin, View):
    '''首页类视图'''
    def get(self, request):

        context = cache.get('index_page_data')
        if context is None:
            # 获取商品分类信息
            types = GoodsType.objects.all()
            # 获取首页轮播图信息
            goods_banners = IndexGoodsBanner.objects.all().order_by('index')
            # 获取首页促销活动信息
            promotion_banners = IndexPromotionBanner.objects.all().order_by('index')
            # 获得首页分类商品展示信息
            # type_goods_banners = IndexGoodsBanner.objects.all()

            for type in types:
                image_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=1).order_by('index')
                title_banners = IndexTypeGoodsBanner.objects.filter(type=type, display_type=0).order_by('index')
                type.image_banners = image_banners
                type.title_banners = title_banners

            context = {'types': types,
                       'goods_banners': goods_banners,
                       'promotion_banners': promotion_banners}

            # 设置缓存数据
            cache.set('index_page_data', context, 3600)
        # 获取购物车商品数列数量
        cart_count = 12

        # 用户登录后获得用户的购物车的数量
        user = request.user
        # 判断用户是否登录
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        # 向context中加入car_count
        context.update(cart_count=cart_count)

        return render(request, 'index.html', context)


# 商品详情列表
class DetailView(View):
    def get(self, request, sku_id):
        # 根据sku_id获取商品的信息
        try:
            sku = GoodsSKU.objects.get(id=sku_id)
        except GoodsSKU.DoesNotExist:
            return redirect(reverse('goods:index'))
        # 获取商品分类信息
        types = GoodsType.objects.all()
        # 获取商品评论信息
        sku_orders = OrderGoods.objects.filter(sku=sku).exclude(comment='')[:30]
        # 获取新品信息
        new_goods = GoodsSKU.objects.filter(type=sku.type).order_by('-create_time')[:2]

        # 获取商品的其他规格
        same_spu_skus = GoodsSKU.objects.filter(goods=sku.goods).exclude(id=sku_id)
        # 获取用户购物车中的数量
        cart_count = 0
        # 组织模板上下文
        user = request.user
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)


            # 添加历史浏览记录
            # conn = get_redis_connection('default')
            history_id = 'history_%d' % user.id
            # 先尝试移除列表中的sku_id
            conn.lrem(history_id, 0, sku_id)
            # 将sku_id 插入到列表左侧
            conn.lpush(history_id, sku_id)
            # 只保留最新浏览的五条记录
            conn.ltrim(history_id, 0, 4)

        context = {
            'sku':sku,
            'types': types,
            'sku_orders': sku_orders,
            'new_goods': new_goods,
            'same_spu_skus': same_spu_skus,
            'cart_count': cart_count
        }
        # 返回数据
        return render(request, 'detail.html', context)


class ListView(View):
    '''商品列表视图'''
    def get(self, request, type_id, page):
        # 根据传来的type_id 寻找对应的种类信息
        try:
            type = GoodsType.objects.get(id=type_id)
        except GoodsType.DoesNotExist:
            # 种类信息不存在时，重定向到首页
            return redirect('goods:index')

        # 获取所有种类信息
        types = GoodsType.objects.all()
        # 获取排序方式
        sort = request.GET.get('sort')

        # 获取商品分类信息
        #三种排序方法
        # sort=='hot' 按照人气又高到低
        # sort=='price' 按照价格由高到低
        # sort==’default' 默认方式排序，用商品id来进行排序
        if sort == 'hot':
            skus = GoodsSKU.objects.filter(type=type).order_by('-sales')
        elif sort=='price':
            skus = GoodsSKU.objects.filter(type=type).order_by('price')
        else:
            skus = GoodsSKU.objects.filter(type=type).order_by('-id')

        # 对数据进行分页
        paginator = Paginator(skus, 1)


        # 对页码进行处理
        try:
            page = int(page)
        except Exception as e:
            page = 1

        # 当传入的页码大于得到的页码时，将页码设为1
        if page > paginator.num_pages:
            page = 1

        # 获取第page的内容，返回Page类的视力对象
        skus_page = paginator.page(page)

        # 获取新品信息
        new_goods = GoodsSKU.objects.filter(type=type).order_by('-create_time')[:2]

        # 获取用户购物车中的数量
        cart_count = 0
        # 组织模板上下文
        user = request.user
        if user.is_authenticated():
            conn = get_redis_connection('default')
            cart_key = 'cart_%d' % user.id
            cart_count = conn.hlen(cart_key)

        # 组织上下文
        context = {
            'type': type,
            'types': types,
            'skus_page': skus_page,
            'new_skus' : new_goods,
            'cart_count': cart_count,
            'sort': sort
        }
        # 返回给模板
        return render(request, 'list.html', context)
