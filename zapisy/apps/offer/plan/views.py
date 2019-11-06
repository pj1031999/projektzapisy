from django.contrib import messages
from django.db import models
from django.shortcuts import render, HttpResponse


def plan_main(request):
    if request.user.is_superuser:
        return render(request, 'plan/plan-main.html')
    else:
        return HttpResponse(status=403)
