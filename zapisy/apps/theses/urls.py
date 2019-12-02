from django.urls import path, include

from . import views

urlpatterns = [
    path("", views.list_all, name="main"),
    path("<int:id>", views.view_thesis, name="selected_thesis"),
    path('<int:id>/edit', views.edit_thesis, name='edit_thesis'),
]
