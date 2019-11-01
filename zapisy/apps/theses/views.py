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


def view_thesis(request, id):
    """
        Show subpage for one thesis
    """

    query = Thesis.objects.filter(id=id)
    thesis = None if len(query)==0 else query[0]

    return render(request, 'theses/thesis.html', {'thesis': thesis})
