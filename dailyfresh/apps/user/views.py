from django.shortcuts import render, redirect,HttpResponse
from django.core.urlresolvers import reverse
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.contrib.auth import authenticate, login,logout
from django.views.generic import View
from utils.mixin import LoginRequiredMixin
from django.conf import settings
from django.core.mail import send_mail
from django_redis import get_redis_connection
from celery_tasks.tasks import send_register_active_email
from itsdangerous import SignatureExpired
from user.models import User, Address
from goods.models import GoodsSKU
import re


# 用户注册页面
def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    else:
        # 接受数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 进行校验
        if not all([username, password, email, allow]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意用户协议'})
        # 进行业务处理
        user = User.objects.create_user(username,  email, password)
        user.is_active = 0
        user.save()
        # 返回应答
        return redirect(reverse('goods:index'))
# # 处理注册信息
# def register_handle(request):
#     # 接受数据
#     username = request.POST.get('username')
#     password = request.POST.get('pwd')
#     email = request.POST.get('email')
#     # 进行校验
#     if all([username, password, email]):
#         return HttpResponse('ok!')
#     # 进行业务处理
#
#     # 返回应答


# 用户注册类视图写
class RegisterView(View):
    # 进入注册页面
    def get(self, request):
        '''显示注册页面'''
        return render(request, 'register.html')

    def post(self, request):
        '''进行注册处理'''
        # 接受数据
        username = request.POST.get('username')
        password = request.POST.get('pwd')
        email = request.POST.get('email')
        allow = request.POST.get('allow')
        # 进行校验
        if not all([username, password, email, allow]):
            return render(request, 'register.html', {'errmsg': '数据不完整'})

        if not re.match(r'^[a-z0-9][\w.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return render(request, 'register.html', {'errmsg': '邮箱格式不正确'})

        if allow != 'on':
            return render(request, 'register.html', {'errmsg': '请同意用户协议'})

        # 查找数据库中用户名是否存在
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # 用户不存在
            user = None
        if user:
            # 用户名已经存在
            return render(request, 'register.html', {'errmsg': '用户名已经存在'})
        # 进行业务处理
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()

        # 发送邮件对已经注册的用户进行激活，要对发送的激活链接进行加密用Serializer的对象来加密
        serializer = Serializer(settings.SECRET_KEY, 3600)
        info = {'confirm': user.id}
        token = serializer.dumps(info)
        token = token.decode()

        # 使用celery发送邮件
        send_register_active_email.delay(email, username, token)


        # 返回应答
        return redirect(reverse('goods:index'))


# 激活账号
class ActiveView(View):
    def get(self, request, token):
        # 解密获取对象的信息
        # 创建加密的对象
        serializer = Serializer(settings.SECRET_KEY, 3600)
        try:
            info = serializer.loads(token)
            # 获取要激活用户的id
            user_id = info['confirm']

            # 根据user_id 获取用户的激活信息
            user = User.objects.get(id = user_id)
            user.is_active = 1
            user.save()

            # 激活后跳转到登录页面
            return redirect(reverse('user:login'))
        except SignatureExpired as e:
            return HttpResponse('激活链接已经失效')


class LoginView(View):
    '''登录'''
    def get(self, request):
        '''显示登录页面'''
        if 'username' in request.COOKIES:
            username = request.COOKIES.get('username')
            checked = 'checked'
        else:
            username = ''
            checked = ''
        return render(request, 'login.html', {'username':username, 'checked': checked})

    def post(self, requset):
        '''验证登录信息正确性'''
        # 获取post请求中的信息
        username = requset.POST.get('username')
        password = requset.POST.get('pwd')

        # 首先验证输入的完整性
        if not all([username, password]):
            return render(requset, 'login.html' ,{'errmsg': '数据不完整'})

        # 业务处理：登录验证
        user = authenticate(username=username, password=password)

        # 用户名和密码正确
        if user is not None:
            if user.is_active:
                # 记住用户的登录状态
                login(requset, user)

                # 获取登录跳转的url地址
                next_url = requset.GET.get('next', reverse('goods:index'))

                # 登录成功返回首页
                response = redirect(next_url)

                # 获取是否记住密码
                remember = requset.POST.get('remember')
                # 若记住密码则设置cookie
                if remember == 'on':
                    response.set_cookie('username', username)
                else:
                    response.delete_cookie('username')

                return response

            else:
                # 用户账号未激活
                return render(requset, 'login.html', {'errmsg':'用户未激活'})
        else:
            # 用户或密码错误
            return render(requset, 'login.html', {'errmsg': '用户名或密码错误'})


class LogoutView(View):
    '''退出'''
    def get(self, request):
        # 退出并清除session信息
        logout(request)
        # 退出后跳转到首页
        return redirect(reverse('goods:index'))


class UserInfoView(LoginRequiredMixin, View):
    '''用户中心'''
    def get(self, request):
        # 显示用户个人信息
        user = request.user
        address = Address.objects.get_default_address(user=user)
        # 用户最近浏览记录
        # 获取浏览过的商品记录
        # 用redis 来储存用户浏览记录，获取时要先跟ｒｅｄｉｓ建立链接
        conn = get_redis_connection('default')

        # 获取对应用户的浏览记录
        list_key = 'history_%d' % user.id
        # 取出ｒｅｄｉｓ中该用户的五条浏览记录
        sku_ids = conn.lrange(list_key, 0, 4)
        # 获取数据库中国对应商品编号的商品ｕｒｌ
        goods_li = []
        for id in sku_ids:
            goods = GoodsSKU.objects.get(id=id)
            goods_li.append(goods)

        context = {'page': 'user', 'user': user, 'address': address,'goods_li': goods_li}
        return render(request, 'user_center_info.html', context)


class UserOrderView(LoginRequiredMixin ,View):
    '''用户中心-订单页面'''
    def get(self, request):
        # 显示用户订单信息
        return render(request, 'user_center_order.html', {'page': 'order'})


class AddressView(LoginRequiredMixin, View):
    '''用户中心-用户地址页面'''
    def get(self, request):
        # 显示用户默认地址
        user = request.user
        # try:
        #     address = Address.addrs.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 没有默认地址
        #     address = None
        # 获取用户的默认地址
        address = Address.objects.get_default_address(user=user)



        # 构造上下文
        context = {'page': 'address', 'address':address}

        return render(request, 'user_center_site.html', context)

    def post(self, request):
        # 获取用户提交的信息
        receiver = request.POST.get('receiver')
        addr = request.POST.get('addr')
        zip_code = request.POST.get('zip_code')
        phone = request.POST.get('phone')

        # 数据校验
        # 如果所输入的数据不完整则跳转到当前页面
        if not all([receiver, addr, phone]):
            return render(request, 'user_center_site.html', {'errmsg':'数据不完整'})

        # 手机号码验证
        if not re.match(r'^1[3|4|5|7|8][0-9]{9}$', phone):
            return render(request, 'user_center_site.html', {'errmsg':'手机号码格式不正确'})

        # 业务处理
        # 如果用户没有默认的收货地址，则将添加的地址设为默认值，否则不做处理

        # 获取登录对向
        user = request.user
        # try:
        #     address = Address.addrs.get(user=user, is_default=True)
        # except Address.DoesNotExist:
        #     # 没有默认地址
        #     address = None
        address = Address.objects.get_default_address(user=user)

        if address:
            is_default = False
        else:
            is_default = True

        # 将地址添加到数据库中
        Address.objects.create(user=user,
                               receiver=receiver,
                               addr=addr,
                               zip_code=zip_code,
                               phone=phone,
                               is_default=is_default)

        # 返回应答
        return redirect(reverse('user:address'))


class UserCartView(LoginRequiredMixin, View):
    '''用户中心-购物车'''
    def get(self, request):
        return render(request, 'cart.html')

