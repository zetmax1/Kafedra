from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/',          views.login_view,             name='login'),
    path('logout/',         views.logout_view,            name='logout'),
    path('dashboard/',      views.dashboard,              name='dashboard'),
    path('sozlamalar/',     views.sozlamalar,             name='sozlamalar'),
    path('umumiy-malumotlar/', views.umumiy_malumotlar,  name='umumiy_malumotlar'),
    path('dashboard/excel-export/', views.dashboard_excel_export, name='dashboard_excel_export'),
    path('api/filtr-variantlar/', views.filtr_variantlar, name='filtr_variantlar'),

    path('parol-tiklash/',
        auth_views.PasswordResetView.as_view(template_name='accounts/parol_tiklash.html'),
        name='password_reset'),
    path('parol-tiklash/yuborildi/',
        auth_views.PasswordResetDoneView.as_view(template_name='accounts/parol_tiklash_yuborildi.html'),
        name='password_reset_done'),
    path('parol-tiklash/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='accounts/parol_yangilash.html'),
        name='password_reset_confirm'),
    path('parol-tiklash/tayyor/',
        auth_views.PasswordResetCompleteView.as_view(template_name='accounts/parol_yangilash_tayyor.html'),
        name='password_reset_complete'),

    path('session-yangilash/', views.session_yangilash, name='session_yangilash'),
]