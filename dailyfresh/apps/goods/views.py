from django.shortcuts import render
from django.views.generic import View


# 首页
def index(request):
    return render(request, 'index.html')


# 商品详情列表
class GoodsListView(View):
    def get(self, request):
        return render(request, 'list.html')