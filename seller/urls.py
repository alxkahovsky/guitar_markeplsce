from django.urls import path
from . import views

app_name = 'seller'

urlpatterns = [
    path('admin/seller/product/add_attrs/<int:product_id>/', views.add_json_attrs, name='add_json_attrs'),
]
