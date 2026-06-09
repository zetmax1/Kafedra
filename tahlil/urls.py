from django.urls import path
from . import views

urlpatterns = [
    path('tahlil/', views.tahlil_list, name='tahlil'),
    path('tahlil/yuklash/', views.excel_yuklash, name='excel_yuklash'),
    path('tahlil/korish/<int:pk>/', views.jadval_korish, name='jadval_korish'),
    path('tahlil/ochirish/<int:pk>/', views.jadval_ochirish, name='jadval_ochirish'),
]