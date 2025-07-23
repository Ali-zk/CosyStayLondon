from django.urls import path
from . import views

app_name = 'shop' # <--- app_name به shop تغییر یافت

urlpatterns = [
    path('products/', views.product_list, name='product_list'), # <--- نام URL به product_list تغییر یافت
    path('products/<int:pk>/', views.product_detail, name='product_detail'), # <--- نام URL به product_detail تغییر یافت
    path('products/add/', views.add_property_view, name='add_property'), # <--- برای افزودن ملک
    
    # --- مسیرهای جدید برای رزرو ---
    #path('products/<int:property_id>/book/', views.book_property, name='book_property'),
    #path('booking/success/<int:booking_id>/', views.booking_success, name='booking_success'),
]