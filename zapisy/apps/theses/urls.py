from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.list_all, name="main"),
    path("<int:id>", views.view_thesis, name="selected_thesis"),
    path("edit/<int:id>", views.edit_thesis, name="edit_thesis"),
    path("new", views.new_thesis, name="new_thesis"),
]
