from django.urls import path
from . import views

urlpatterns = [
    path('', views.plan_view, name='plan-view'),
    path('create/', views.plan_create, name='plan-create'),
]
