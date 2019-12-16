import json

from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.decorators import employee_required
from django.utils import timezone
from apps.theses.models import Thesis
from apps.theses.enums import ThesisKind, ThesisStatus
from apps.theses.users import is_theses_board_member
from apps.theses.forms import ThesisForm, EditThesisForm
from apps.users.models import BaseUser, Employee


@login_required
def list_all(request):
    theses = Thesis.objects.all()
    board_member = is_theses_board_member(request.user)

    visible_theses = [
        thesis for thesis in theses if thesis.can_see_thesis(request.user)]

    thesis_list = []
    for p in visible_theses:
        title = p.title
        is_available = not p.is_reserved
        kind = p.get_kind_display()
        status = p.get_status_display()
        has_been_accepted = p.has_been_accepted
        advisor = p.advisor.__str__()
        url = reverse('theses:selected_thesis', None, [str(p.id)])

        record = {"id": p.id, "title": title, "is_available": is_available, "kind": kind,
                  "status": status, "has_been_accepted": has_been_accepted, "url": url,
                  "advisor": advisor}

        thesis_list.append(record)

    return render(request, 'theses/list_all.html', {
        'theses_json': json.dumps(thesis_list),
        'theses': visible_theses,
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

    thesis = get_object_or_404(Thesis, id=id)
    if request.method == "POST":
        thesis_status = thesis.status
        form = EditThesisForm(request.user, request.POST, instance=thesis)
        # check whether it's valid:
        if form.is_valid():
            post = form.save(commit=False)
            post.modified = timezone.now()
            post.status = thesis_status
            post.save()
            form.save_m2m()
            messages.success(request, 'Zapisano zmiany')
            return redirect('theses:selected_thesis', id=id)
    else:
        form = EditThesisForm(request.user, instance=thesis)

    return render(request, 'theses/thesis_form.html', {'thesis_form': form})


@login_required
@employee_required
def new_thesis(request):
    """
        Show form for create new thesis
    """

    new_thesis = True
    if request.method == "POST":
        form = ThesisForm(request.user, request.POST)
        # check whether it's valid:
        if form.is_valid():
            post = form.save(commit=False)
            post.status = ThesisStatus.BEING_EVALUATED.value
            post.added = timezone.now()
            post.save()
            messages.success(request, 'Dodano nową pracę')
            return redirect('/theses')
    else:
        form = ThesisForm(request.user)

    return render(request, 'theses/thesis_form.html', {'thesis_form': form, 'new_thesis': new_thesis})
