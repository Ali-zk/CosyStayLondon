from django.urls import path
from . import views

app_name = "home"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path("product/", views.ProductView.as_view(), name="product"),
]
