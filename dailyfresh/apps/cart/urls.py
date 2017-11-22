from django.conf.urls import url
from cart.views import CartAddView ,CartInfoView, CartUpdateView, CartDeletView


urlpatterns = [
    url('^add$', CartAddView.as_view(), name='add'),  # 购物车记录添加
    url('^$', CartInfoView.as_view(), name='cart'),  # 购物车页面显示
    url('^update$', CartUpdateView.as_view(), name='update'),  # 购物车记录增加
    url('^delete$', CartDeletView.as_view(), name='delete'),  # 购物车记录删除
]