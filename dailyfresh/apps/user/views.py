from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.views.generic import View
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
        return render(request, 'register.html')

    def post(self, request):
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
        user = User.objects.create_user(username, email, password)
        user.is_active = 0
        user.save()
        # 返回应答
        return redirect(reverse('goods:index'))