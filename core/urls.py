from django.urls import path
from . import views
from core.admin import admin

from django.conf import settings


urlpatterns = [
    path('issues/', views.issue_list, name='issue_list'),
    path('issues/add/', views.issue_create, name='issue_create'),
    path('issues/<str:pk>/', views.issue_detail, name='issue_detail'),
    path('issues/<str:pk>/edit/', views.issue_update, name='issue_update'),
    path('issues/<str:pk>/delete/', views.issue_delete, name='issue_delete'),
]