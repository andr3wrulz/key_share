from django.urls import path

from . import views

urlpatterns = [
    path('', views.key_list, name='key_list'),
    path('key/<int:pk>/', views.key_detail, name='key_detail'),
    path('key/<int:pk>/edit/', views.key_edit, name='key_edit'),
    path('key/<int:pk>/delete/', views.key_delete, name='key_delete'),
    path('key/<int:pk>/redeem/', views.key_redeem, name='key_redeem'),
    path('key/new/', views.key_new, name='key_new'),
]