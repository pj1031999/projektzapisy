from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.list_all, name="main"),
    path("list_all.html", views.list_all, name="main"),
]
