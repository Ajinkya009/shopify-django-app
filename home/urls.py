from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='root_path'),
    path('clear-session/', views.clear_session, name='clear_session'),
    path('store-days-time/', views.store_days_time, name='store_days_time'),
]
