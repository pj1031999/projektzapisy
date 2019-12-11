from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.users.decorators import employee_required
from django.utils import timezone
from apps.theses.models import Thesis
from apps.theses.enums import ThesisKind, ThesisStatus
from apps.theses.users import is_theses_board_member
from apps.theses.forms import ThesisForm
from apps.users.models import BaseUser, Employee

@login_required
def list_all(request):
    theses = Thesis.objects.all()
    board_member = is_theses_board_member(request.user)

    filtered_theses = [thesis for thesis in theses if thesis.can_see_thesis(request.user)]

    return render(request, 'theses/list_all.html', {
        'theses': filtered_theses,
        'board_member': board_member,
    })


@login_required
def view_thesis(request, id):
    """
        Show subpage for one thesis
    """

    query = Thesis.objects.filter(id=id)
    thesiskind = {int(i): i.display for i in ThesisKind}
    thesis = None if len(query) == 0 else query[0]
    board_member = is_theses_board_member(request.user)

    return render(request, 'theses/thesis.html', {'thesis': thesis, 'thesiskind': thesiskind,
                                                  'board_member': board_member})


@login_required
@employee_required
def edit_thesis(request, id):
    """
        Show form for edit selected thesis
    """
    query = Thesis.objects.filter(id=id)
    thesiskind = {int(i): i.display for i in ThesisKind}
    thesis = None if len(query) == 0 else query[0]
    board_member = is_theses_board_member(request.user)

    return render(request, 'theses/thesis_form.html', {'thesis': thesis, 'thesiskind': thesiskind,
                                                  'board_member': board_member})


@login_required
@employee_required
def new_thesis(request):
    """
        Show form for create new thesis
    """
    if request.method == "POST":
        form = ThesisForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            post = form.save(commit=False)
            post.status = ThesisStatus.BEING_EVALUATED.value
            post.added = timezone.now()

            post.save()
            return redirect('theses:main')
    else:
        if request.user.is_staff:
            form = ThesisForm()
        else:
            form = ThesisForm(default_advisor=True, initial={"advisor": request.user.employee})

    return render(request, 'theses/new_thesis.html', {'thesis_form': form})
