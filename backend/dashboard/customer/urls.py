from django.urls import path, include
from . import views

app_name = "customer"

urlpatterns = [
    path('home/', views.CustomerDashboardHomeView.as_view(), name='home'),
    path('edit/profile/', views.CustomerProfileEditView.as_view(), name='edit-profile'),
    path('change/password/', views.CustomerPasswordChangeView.as_view(), name='change-password'),
    path('bookings/', views.CustomerMyBookingsView.as_view(), name='my-bookings'),
    path('logout/', views.LogoutView.as_view(), name='logout'),

                                  
]