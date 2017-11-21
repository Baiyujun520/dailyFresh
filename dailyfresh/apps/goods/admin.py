from django.contrib import admin
from django.core.cache import cache
from goods.models import GoodsType, GoodsSKU, Goods, GoodsImage, IndexGoodsBanner, IndexTypeGoodsBanner, IndexPromotionBanner
# Register your models here.


class BaseModelAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        '''当新增或修改了数据库中的内容时会调用该方法'''
        # 调用父类的方法
        super().save_model(request, obj, form, change)

        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()  # 会重新生成静态页面

        # 当重新生成静态页面之后，会自动清除缓存，再登录的时候若缓存为none，则会自动查询一下数据库
        cache.delete('index_page_data')


    def delete_model(self, request, obj):
        '''当删除表中的数据时候会调用该方法'''
        # 调用父类的方法
        super().delete_model(request, obj)

        from celery_tasks.tasks import generate_static_index_html
        generate_static_index_html.delay()

        cache.delete('index_page_data')


class IndexPromotionBannerAdmin(BaseModelAdmin):
    pass


class IndexGoodsBannerAdmin(BaseModelAdmin):
    pass


class GoodsTypeAdmin(BaseModelAdmin):
    pass


class IndexTypeGoodsBannerAdmin(BaseModelAdmin):
    pass

admin.site.register(GoodsType, GoodsTypeAdmin)
admin.site.register(IndexGoodsBanner, IndexGoodsBannerAdmin)
admin.site.register(IndexTypeGoodsBanner, IndexTypeGoodsBannerAdmin)
admin.site.register(IndexPromotionBanner, IndexPromotionBannerAdmin)

# admin.site.register(GoodsSKU)
# admin.site.register(Goods)
# admin.site.register(GoodsImage)