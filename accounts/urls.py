from django.urls import path
from . import views

urlpatterns = [
    path('Login/', views.Login, name='Login'),
    path('Logout/', views.Logout, name='Logout'),

    path('users/', views.user_list, name='user_list'),
    path('users/add/', views.user_add, name='user_add'),
    path('users/<int:pk>/', views.user_detail, name='user_detail'),
    path('users/<int:pk>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:pk>/toggle-active/', views.user_toggle_active, name='user_toggle_active'),
    path('users/<int:pk>/reset-password/', views.user_reset_password, name='user_reset_password'),
]