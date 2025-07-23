from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    path('resend-code/', views.resend_verification_code, name='resend_verification_code'),
]
