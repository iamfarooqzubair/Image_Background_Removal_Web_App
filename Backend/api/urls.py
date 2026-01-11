"""
API URL configuration
"""
from django.urls import path
from . import views

urlpatterns = [
    path('remove-background/', views.RemoveBackgroundView.as_view(), name='remove-background'),
    path('resize-image/', views.ResizeImageView.as_view(), name='resize-image'),
    path('health/', views.health_check, name='health-check'),
]
