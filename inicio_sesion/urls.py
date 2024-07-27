from django.urls import path
from . import views

urlpatterns = [
    path('', views.iniciar_sesion, name='iniciar_sesion'),
    path('video_feed/', views.video_feed, name='video_feed'),
    path('check_success/', views.check_success, name='check_success'),
]
