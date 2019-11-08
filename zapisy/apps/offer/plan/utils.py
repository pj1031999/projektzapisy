from datetime import date
from django.db import models
from django.db.models import Sum, Q

from apps.offer.vote.models.single_vote import SingleVote, SingleVoteQuerySet
from apps.offer.vote.models.system_state import SystemState
from functools import reduce


def get_votes(years: int) -> SingleVoteQuerySet:
    # Returns SingleVoteQuerySet.
    # years arguments specifies how many years we want to collect votes from
    # Each item is a dictionary with such fields:
    # 'proposal__name'     - name of course
    # 'state__year'        - year of vote
    # 'proposal__semester' - semester of course
    # 'total'              - number of points course gathered from all votes
    states = SystemState.objects.all().order_by('-year')
    current_year = SystemState.get_current_state().year
    year_list = [current_year]

    for (i, state) in enumerate(states):
        print(str(i) + '\n')
        if i >= years:
            break
        elif state.year != current_year:
            year_list.append(state.year)

    votes = SingleVote.objects.all().filter(
        reduce(lambda x, y: x | y, [Q(state__year=year) for year in year_list]), value__gt=0).values(
            'proposal__name', 'state__year', 'proposal__semester').annotate(total=Sum('value')).order_by('proposal__name', 'state__year')
    # Here we create sql query that looks somewhat like this:
    # SELECT proposal__name, state__year, proposal__semester, SUM(value) FROM ...
    # .
    # .
    # .
    # WHERE state__year=year1 OR state__year=year2 OR ... AND value > 0
    # GROUP BY proposal__name, state__year, proposal__semester
    # ORDER BY proposal__name, state__year
    return votes
