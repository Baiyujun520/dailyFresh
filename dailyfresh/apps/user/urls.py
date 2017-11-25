from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from user.views import RegisterView, ActiveView, LoginView,LogoutView, UserInfoView, UserOrderView, AddressView

urlpatterns = [
    # url(r'^register$', views.register, name='register'),
    url(r'^register$', RegisterView.as_view(), name='register'),  # 注册
    url(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),  # 激活
    url(r'^login$', LoginView.as_view(), name='login'),
    url(r'^logout$', LogoutView.as_view(), name='logout'),  # 退出当前用户
    # url(r'^$', login_required(UserInfoView.as_view()), name='user'),  # 用户中心-用户信息
    # url(r'^order$', login_required(UserOrderView.as_view()), name='order'),  # 用户中心-订单信息
    # url(r'^address$', login_required(AddressView.as_view()), name='address'),  # 用户中心-用户地址管理
    url(r'^$', UserInfoView.as_view(), name='user'),  # 用户中心-用户信息
    url(r'^order/(?P<page>\d+)$', UserOrderView.as_view(), name='order'),  # 用户中心-订单信息
    url(r'^address$', AddressView.as_view(), name='address'),  # 用户中心-用户地址管理
]
