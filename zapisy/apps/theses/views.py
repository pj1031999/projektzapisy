import json
import tempfile
import os


from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from operator import itemgetter
from django.http import HttpResponse
from django.template import Context
from django.template.loader import get_template
from django.core.exceptions import PermissionDenied
from xhtml2pdf import pisa


from apps.theses.enums import ThesisKind, ThesisStatus, ThesisVote
from apps.theses.forms import EditThesisForm, RemarkForm, ThesisForm, VoteForm
from apps.theses.models import Remark, Thesis, Vote
from apps.theses.users import get_theses_board, is_theses_board_member
from apps.theses.system_settings import change_status
from apps.users.decorators import employee_required
from apps.users.models import BaseUser, Employee, Student


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
        is_mine = p.is_mine(request.user) or p.is_student_assigned(
            request.user) or p.is_supporting_advisor_assigned(request.user)
        advisor = p.advisor.__str__()
        url = reverse('theses:selected_thesis', None, [str(p.id)])

        record = {"id": p.id, "title": title, "is_available": is_available, "kind": kind,
                  "status": status, "has_been_accepted": has_been_accepted, "is_mine": is_mine, "url": url,
                  "advisor": advisor, "modified": p.modified.timestamp()}

        thesis_list.append(record)

    return render(request, 'theses/list_all.html', {
        'theses_json': json.dumps(thesis_list),
        'board_member': board_member,
    })


@login_required
def view_thesis(request, id):
    """
        Show subpage for one thesis
    """

    thesis = get_object_or_404(Thesis, id=id)
    board_member = is_theses_board_member(request.user)
    can_see_remarks = (
        board_member or request.user.is_staff or thesis.is_mine(request.user))
    can_edit_thesis = (request.user.is_staff or thesis.is_mine(request.user))
    not_has_been_accepted = not thesis.has_been_accepted

    if not_has_been_accepted and not request.user.is_staff and not thesis.is_mine(request.user) and not thesis.is_supporting_advisor_assigned(request.user):
        raise PermissionDenied

    students = []
    for student in thesis.students.all():
        students.append({'name': student.__str__(), 'id': student.id})

    all_voters = get_theses_board()
    votes = []
    for vote in thesis.thesis_votes.all():
        votes.append({'owner': vote.owner,
                      'vote': vote.get_vote_display()})

    for voter in all_voters:
        try:
            thesis.thesis_votes.get(owner=voter)
        except Vote.DoesNotExist:
            votes.append({'owner': voter,
                          'vote': ThesisVote.NONE.display})

    for vote in votes:
        if vote['owner'].user == request.user:
            votes.remove(vote)
            votes.insert(0, vote)

    remarks = None

    if board_member and not_has_been_accepted:
        remarks = thesis.thesis_remarks.all().exclude(
            author=request.user.employee)
    elif can_see_remarks:
        remarks = thesis.thesis_remarks.all()

    remarkform = None

    if board_member:
        try:
            remark = thesis.thesis_remarks.all().get(author=request.user.employee)
        except Remark.DoesNotExist:
            remark = None

        # edit existing remark
        if remark:
            if request.method == "POST":
                remarkform = RemarkForm(request.POST, instance=remark)
                if remarkform.is_valid():
                    post = remarkform.save(commit=False)
                    post.modified = timezone.now()
                    post.thesis = thesis
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
                    post.thesis = thesis
                    post.save()

                    messages.success(request, 'Zapisano uwagę')
                    return redirect('theses:selected_thesis', id=id)
            else:
                remarkform = RemarkForm()

    return render(request, 'theses/thesis.html', {'thesis': thesis,
                                                  'students': students,
                                                  'board_member': board_member,
                                                  'can_see_remarks': can_see_remarks,
                                                  'can_edit_thesis': can_edit_thesis,
                                                  'not_has_been_accepted': not_has_been_accepted,
                                                  'remarks': remarks,
                                                  'remark_form': remarkform,
                                                  'votes': votes})


@login_required
def gen_pdf(request, id, studentid):
    thesis = get_object_or_404(Thesis, id=id)
    try:
        first_student = thesis.students.get(id=studentid)
    except Student.DoesNotExist:
        raise Http404("No Student matches the given query.")

    if not request.user.is_staff and not thesis.is_mine(request.user) and not thesis.is_student_assigned(request.user) and not thesis.is_supporting_advisor_assigned(request.user):
        raise PermissionDenied

    first_student = {'name': first_student.__str__(
    ), 'matricula': first_student.matricula}

    students = []
    for student in thesis.students.all():
        if(student.id != studentid):
            students.append({'name': student.__str__(),
                             'matricula': student.matricula})

    students_num = len(students) + 1

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="dokument.pdf"'

    context = {'thesis': thesis, 'first_student': first_student,
               'students': students,
               'students_num': students_num}

    template = get_template('theses/form_pdf.html')
    html = template.render(context=context)

    pdf = pisa.CreatePDF(html.encode('utf-8'),
                         dest=response, encoding='utf-8')
    if pdf.err:
        return HttpResponse("We had some errors!")

    return response


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
        vote = thesis.thesis_votes.get(owner=request.user.employee)
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
                post.thesis = thesis
            post.save()

            # check number of votes and change thesis status
            change_status(thesis)

            messages.success(request, 'Zapisano głos')
            return redirect('theses:selected_thesis', id=id)
    elif vote:
        form = VoteForm(instance=vote)
    else:
        form = VoteForm()

    return render(request, 'theses/vote.html', {'vote_form': form, 'thesis': thesis})
