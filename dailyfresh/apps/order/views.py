from django.shortcuts import render
from django.views.generic import View
from utils.mixin import LoginRequiredMixin
from django.http import JsonResponse
# Create your views here.
# 订单页面

class OrderPlaceView(LoginRequiredMixin, View):
    def post(self, request):
        user = request.user
        # 接收数据u
        skus = request.POST.getlist('sku_id')
        print(skus)