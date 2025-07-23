from django.urls import path, include
from . import views # فرض می‌کنیم DashboardHomeView در views.py همین اپلیکیشن است

app_name = "admin"

urlpatterns = [
    path('home/', views.AdminDashboardHomeView.as_view(), name='home'),
    path('security-edit/', views.AdminSecurityEditView.as_view(), name='security-edit'),
    path('profile/', views.AdminProfileUpdateView.as_view(), name='profile'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

                      
    path('users/', views.AdminUserListView.as_view(), name='user-list'),
    path('users/add/', views.AdminUserCreateView.as_view(), name='user-create'),
    path('users/<int:pk>/edit/', views.AdminUserUpdateView.as_view(), name='user-update'),
    path('users/<int:pk>/delete/', views.AdminUserDeleteView.as_view(), name='user-delete'),


    path('properties/', views.AdminPropertyListView.as_view(), name='property-list'),
    path('properties/add/', views.AdminPropertyCreateView.as_view(), name='property-create'),
    path('properties/<int:pk>/edit/', views.AdminPropertyUpdateView.as_view(), name='property-update'),
    path('properties/<int:pk>/delete/', views.AdminPropertyDeleteView.as_view(), name='property-delete'),

    path('property/', include('dashboard.admin.property.urls')),

   
    path('carts/', views.AdminCartListView.as_view(), name='cart-list'),
    path('carts/add/', views.AdminCartCreateView.as_view(), name='cart-create'),
    path('carts/<int:pk>/edit/', views.AdminCartUpdateView.as_view(), name='cart-update'),
    path('carts/<int:pk>/delete/', views.AdminCartDeleteView.as_view(), name='cart-delete'),

    
    path('cart-items/', views.AdminCartItemListView.as_view(), name='cartitem-list'),
    path('cart-items/add/', views.AdminCartItemCreateView.as_view(), name='cartitem-create'),
    path('cart-items/<int:pk>/edit/', views.AdminCartItemUpdateView.as_view(), name='cartitem-update'),
    path('cart-items/<int:pk>/delete/', views.AdminCartItemDeleteView.as_view(), name='cartitem-delete'),

  
    path('orders/', views.AdminOrderListView.as_view(), name='order-list'),
    path('orders/add/', views.AdminOrderCreateView.as_view(), name='order-create'),
    path('orders/<int:pk>/edit/', views.AdminOrderUpdateView.as_view(), name='order-update'),
    path('orders/<int:pk>/delete/', views.AdminOrderDeleteView.as_view(), name='order-delete'),

    
    path('order-items/', views.AdminOrderItemListView.as_view(), name='orderitem-list'),
    path('order-items/add/', views.AdminOrderItemCreateView.as_view(), name='orderitem-create'),
    path('order-items/<int:pk>/edit/', views.AdminOrderItemUpdateView.as_view(), name='orderitem-update'),
    path('order-items/<int:pk>/delete/', views.AdminOrderItemDeleteView.as_view(), name='orderitem-delete'),
]            
                                  
