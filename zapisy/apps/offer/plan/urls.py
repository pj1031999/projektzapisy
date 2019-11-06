from django.urls import path
from . import views

urlpatterns = [
    path('', views.plan_main, name='plan-main'),
]
