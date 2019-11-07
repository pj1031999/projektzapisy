from django.shortcuts import render, HttpResponse
from apps.users.models import BaseUser


def plan_view(request):
    if request.user.is_superuser or BaseUser.is_employee(request.user):
        return render(request, 'plan/view-plan.html')
    else:
        return HttpResponse(status=403)


def plan_create(request):
    if request.user.is_superuser:
        return render(request, 'plan/create-plan.html')
    else:
        return HttpResponse(status=403)