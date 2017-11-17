from django.conf.urls import url
from goods.views import index, GoodsListView

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^list$', GoodsListView.as_view(), name='list'),  # 商品详情列表
]