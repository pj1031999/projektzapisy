from datetime import date
from django.db import models
from django.db.models import Sum

from apps.offer.vote.models.single_vote import SingleVote, SingleVoteQuerySet
from apps.offer.vote.models.system_state import SystemState


def get_votes(years: int) -> SingleVoteQuerySet:
    # Returns SingleVoteQuerySet. Each item is a dictionary witch such fields:
    # 'proposal__name'     - name of course
    # 'state__year'        - year of vote
    # 'proposal__semester' - semester of course
    # 'total'              - number of points course gathered from all votes
    current_year = date.today().year
    votes = SingleVote.objects.all().filter(
        state__year__gt=current_year - years, value__gt=0).values(
            'proposal__name', 'state__year', 'proposal__semester').annotate(total=Sum('value')).order_by('proposal__name', 'state__year')
    # Here we create sql query that looks somewhat like this:
    # SELECT proposal__name, state__year, proposal__semester, SUM(value) FROM ...
    # .
    # .
    # .
    # WHERE state__year > current_year - years AND value > 0
    # GROUP BY proposal__name, state__year, proposal__semester
    # ORDER BY proposal__name, state__year
    return votes
