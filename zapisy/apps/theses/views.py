import json

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.theses.enums import ThesisKind, ThesisStatus, ThesisVote
from apps.theses.forms import EditThesisForm, RemarkForm, ThesisForm, VoteForm
from apps.theses.models import Remark, Thesis, Vote, get_theses_system_settings
from apps.theses.users import get_theses_board, is_theses_board_member
from apps.users.decorators import employee_required
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
        is_mine = p.is_mine(request.user)
        advisor = p.advisor.__str__()
        url = reverse('theses:selected_thesis', None, [str(p.id)])

        record = {"id": p.id, "title": title, "is_available": is_available, "kind": kind,
                  "status": status, "has_been_accepted": has_been_accepted, "is_mine": is_mine, "url": url,
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

    thesis = get_object_or_404(Thesis, id=id)
    thesiskind = {int(i): i.display for i in ThesisKind}
    board_member = is_theses_board_member(request.user)
    can_see_remarks = (board_member or request.user.is_staff or
                       request.user == thesis.advisor or
                       request.user == thesis.supporting_advisor)
    all_voters = get_theses_board()
    votes = []
    for vote in thesis.votes.all():
        votes.append({'owner': vote.owner,
                      'vote': vote.get_vote_display()})
    for voter in all_voters:
        try:
            thesis.votes.get(owner=voter)
        except Vote.DoesNotExist:
            votes.append({'owner': voter,
                          'vote': ThesisVote.NONE.display})

    remarks = None

    if board_member:
        remarks = thesis.remarks.exclude(author=request.user.employee)
    elif can_see_remarks:
        remarks = thesis.remarks.all()

    remarkform = None

    if board_member:
        try:
            remark = thesis.remarks.get(author=request.user.employee)
        except Remark.DoesNotExist:
            remark = None

        # edit existing remark
        if remark:
            if request.method == "POST":
                remarkform = RemarkForm(request.POST, instance=remark)
                if remarkform.is_valid():
                    post = remarkform.save(commit=False)
                    post.modified = timezone.now()
                    post.save()
                    messages.success(request, 'Zapisano uwagę')
                    return redirect('theses:selected_thesis', id=id)
            else:
                remarkform = RemarkForm(instance=remark)

        # create new remark and add to remarks in thesis
        else:
            if request.method == "POST":
                remarkform = RemarkForm(request.POST)
                if remarkform.is_valid():
                    post = remarkform.save(commit=False)
                    post.modified = timezone.now()
                    post.author = request.user.employee
                    post.save()

                    new_remark = Remark.objects.get(pk=post.pk)
                    thesis.remarks.add(new_remark)

                    messages.success(request, 'Zapisano uwagę')
                    return redirect('theses:selected_thesis', id=id)
            else:
                remarkform = RemarkForm()

    return render(request, 'theses/thesis.html', {'thesis': thesis, 'thesiskind': thesiskind,
                                                  'board_member': board_member,
                                                  'can_see_remarks': can_see_remarks,
                                                  'remarks': remarks,
                                                  'remark_form': remarkform,
                                                  'votes': votes})


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
            if not request.user.is_staff:
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

    return render(request, 'theses/thesis_form.html', {'thesis_form': form, 'new_thesis': True})


@login_required
@employee_required
def vote_for_thesis(request, id):
    """
        Show vote form for selected thesis
    """

    if not is_theses_board_member(request.user):
        raise Http404

    thesis = get_object_or_404(Thesis, id=id)

    try:
        vote = thesis.votes.get(owner=request.user.employee)
    except Vote.DoesNotExist:
        vote = None

    if request.method == "POST":
        if vote:
            form = VoteForm(request.POST, instance=vote)
        else:
            form = VoteForm(request.POST)

        if form.is_valid():
            post = form.save(commit=False)
            if not vote:
                post.owner = request.user.employee
            post.save()

            if not vote:
                new_vote = Vote.objects.get(pk=post.pk)
                thesis.votes.add(new_vote)

            #check number of votes and change thesis status
            settings_instance = get_theses_system_settings()
            if settings_instance:
                settings_instance.change_status(thesis)

            messages.success(request, 'Zapisano głos')
            return redirect('theses:selected_thesis', id=id)
    elif vote:
        form = VoteForm(instance=vote)
    else:
        form = VoteForm()

    return render(request, 'theses/vote.html', {'vote_form': form, 'thesis': thesis})
