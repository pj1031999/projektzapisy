from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.theses.models import Thesis
from apps.theses.enums import ThesisKind
from apps.theses.enums import ThesisStatus
from apps.theses.users import is_theses_board_member
from apps.users.models import BaseUser

def can_see_thesis(thesis, user):
    return ((thesis.status != ThesisStatus.BEING_EVALUATED and thesis.status != ThesisStatus.RETURNED_FOR_CORRECTIONS) 
    or is_theses_board_member(user)
    or user == (thesis.advisor.user if thesis.advisor != None else None)
    or user == (thesis.supporting_advisor.user if thesis.supporting_advisor != None else None)
    or user.is_staff)

@login_required
def list_all(request):
    theses = Thesis.objects.all()

    filtered_theses = [thesis for thesis in theses if can_see_thesis(thesis, request.user)]

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
