from django.conf.urls import url
from order.views import OrderPlaceView, OrderCommitView, OrderPayView, CheckPayView, CommentView
urlpatterns = [
    url(r'^place$', OrderPlaceView.as_view(), name='place'),  # 提交订单页
    url(r'^commit$', OrderCommitView.as_view(), name='commit'),  # 提交订单
    url(r'^pay$', OrderPayView.as_view(), name='pay'),  # 订单支付页面
    url(r'^check$', CheckPayView.as_view(), name='check'), # 订单结果
    url(r'^comment/(?P<order_id>.+)$', CommentView.as_view(), name='comment'),# 评论页面
]