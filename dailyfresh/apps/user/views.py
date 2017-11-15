from django.shortcuts import render, redirect,HttpResponse
from django.core.urlresolvers import reverse
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from django.views.generic import View
from django.conf import settings
from django.core.mail import send_mail
from celery_tasks.tasks import  send_register_active_email
from itsdangerous import SignatureExpired
from user.models import User
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
        send_register_active_email(email, username, token)


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
            return render(request, 'login.html')
        except SignatureExpired as e:
            return HttpResponse('激活链接已经失效')

