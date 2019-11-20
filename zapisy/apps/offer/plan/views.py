from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from apps.users.models import BaseUser
from django.urls import reverse

from apps.offer.plan.utils import get_votes


def plan_view(request):
    if request.user.is_superuser or BaseUser.is_employee(request.user):
        return render(request, 'plan/view-plan.html')
    else:
        return HttpResponse(status=403)


def plan_create(request):
    if request.user.is_superuser:
        courses_proposal = get_votes(1)
        courses = []
        for key, value in courses_proposal.items():
            for k, v in value.items():
                # First value is the name of course
                # Second value is the semester when the course is planned to be
                # Third value says if this course is proposed
                courses.append([key, v['semester'], False])

        context = {'courses_proposal': courses}
        return render(request, 'plan/create-plan.html', context)
    else:
        return HttpResponse(status=403)


def plan_vote(request):
    return HttpResponseRedirect(reverse('plan-create'))
