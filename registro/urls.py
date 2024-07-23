from django.urls import path
from . import views

urlpatterns = [
    path('', views.registro, name='registro'),
      path('video_capture/', views.video_capture, name='video_capture'),
]