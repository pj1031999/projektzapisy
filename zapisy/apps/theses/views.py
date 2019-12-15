from django.conf import settings
from django.urls import reverse
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.users.decorators import employee_required
from django.utils import timezone
from apps.theses.models import Thesis, Remark
from apps.theses.enums import ThesisKind, ThesisStatus
from apps.theses.users import is_theses_board_member
from apps.theses.forms import ThesisForm, EditThesisForm, RemarkForm
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

    thesis = get_object_or_404(Thesis, id=id)
    thesiskind = {int(i): i.display for i in ThesisKind}
    board_member = is_theses_board_member(request.user)
    can_see_remarks = board_member or request.user.is_staff \
                      or request.user == thesis.advisor \
                      or request.user == thesis.supporting_advisor
    remarks = None

    if board_member:
        remarks = thesis.remarks.exclude(author=request.user.employee)
    elif can_see_remarks:
        remarks = thesis.remarks.all()

    form = None

    if board_member:
        try:
            remark = thesis.remarks.get(author=request.user.employee)
        except:
            remark = None
        #edit existing remark
        if remark:
            if request.method == "POST":
                form = RemarkForm(request.POST, instance=remark)
                if form.is_valid():
                    post = form.save(commit=False)
                    post.modified = timezone.now()
                    post.save()
                    messages.success(request, 'Zapisano uwagę')
                    return redirect('theses:selected_thesis', id=id)
            else:
                form = RemarkForm(instance=remark)

        #create new remark and add to remarks in thesis
        else:
            if request.method == "POST":
                form = RemarkForm(request.POST)
                if form.is_valid():
                    post = form.save(commit=False)
                    post.modified = timezone.now()
                    post.author = request.user.employee
                    post.save()

                    new_remark = Remark.objects.get(pk=post.pk)
                    thesis.remarks.add(new_remark)

                    messages.success(request, 'Zapisano uwagę')
                    return redirect('theses:selected_thesis', id=id)
            else:
                form = RemarkForm()

    return render(request, 'theses/thesis.html', {'thesis': thesis, 'thesiskind': thesiskind,
                                                  'board_member': board_member,
                                                  'can_see_remarks': can_see_remarks,
                                                  'remarks': remarks,
                                                  'remark_form': form})


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
