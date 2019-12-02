from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.theses.models import Thesis
from apps.theses.enums import ThesisKind
from apps.theses.enums import ThesisStatus
from apps.users.models import BaseUser

@login_required
def list_all(request):
    theses = Thesis.objects.all()

    filtered_theses = [thesis for thesis in theses if thesis.can_see_thesis(request.user)]

    return render(request, 'theses/list_all.html', {
        'theses': filtered_theses,
    })


@login_required
def view_thesis(request, id):
    """
        Show subpage for one thesis
    """

    query = Thesis.objects.filter(id=id)
    thesiskind = {int(i): i.display for i in ThesisKind}
    thesis = None if len(query) == 0 else query[0]

    return render(request, 'theses/thesis.html', {'thesis': thesis, 'thesiskind': thesiskind})
