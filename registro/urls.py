from django.urls import path
from . import views

urlpatterns = [
    path('', views.registro, name='registro'),
    path('video_capture/', views.video_capture, name='video_capture'),
    path('video_feed/', views.gen_frames, name='video_feed'),
    path('success/', views.success_page, name='success_page'),
]