from django.urls import path
from . import views

urlpatterns = [
    path('hisobotlar/', views.hisobotlar_list, name='hisobotlar'),
    path('hisobotlar/yuklash/', views.pdf_yuklash, name='pdf_yuklash'),
    path('hisobotlar/natija/<int:pk>/', views.natija, name='natija'),
    path('hisobotlar/excel/<int:pk>/', views.excel_yuklab_olish, name='excel_yuklab_olish'),
    path('hisobotlar/ochirish/<int:pk>/', views.pdf_ochirish, name='pdf_ochirish'),
    path('hisobotlar/barchani-ochirish/', views.pdf_barchani_ochirish, name='pdf_barchani_ochirish'),
]