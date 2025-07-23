# cart/urls.py
from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('add-from-session/', views.add_from_session, name='add_from_session'),
    path('view/', views.view_cart, name='view_cart'), 
    path('remove-item/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('my-orders/', views.my_orders, name='my_orders'),
    
    # Payment URLs
    path('payment/<int:order_id>/', views.payment_page, name='payment_page'),
    path('payment/confirm/', views.confirm_payment, name='confirm_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    
    # Webhook
    path('stripe-webhook/', views.stripe_webhook, name='stripe_webhook'),
]