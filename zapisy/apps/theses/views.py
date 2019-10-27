from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from django.shortcuts import render
from apps.theses.models import Thesis


def list_all(request):
    theses = Thesis.objects.all()

    return render(request, 'theses/list_all.html', {
        'theses': theses,
    })
