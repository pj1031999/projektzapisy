from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from django.shortcuts import render


def list_all(request):
    """
        Temporarily list all theses
    """

    return render(request, 'theses/list_all.html')
