from datetime import date
from django.db import models
from django.db.models import Sum, Q, Count, Value
from django.db.models.functions import Concat

from apps.offer.vote.models.single_vote import SingleVote, SingleVoteQuerySet
from apps.offer.vote.models.system_state import SystemState
from apps.enrollment.courses.models.course_instance import CourseInstance
from apps.offer.proposal.models import Proposal
from apps.enrollment.records.models.records import Record, RecordStatus
from apps.enrollment.courses.models.group import Group

from functools import reduce
from typing import List

import gspread
from oauth2client.service_account import ServiceAccountCredentials


def get_votes(years: int):
    # years argument specifies how many years back we want to collect data from.
    # Return value: Dict[str, Dict[str, Dict[...]]]
    # Each dictionary entry describes a various data about course in a single year, whether it was already taught or is still
    # voted upon.
    # This dictionary is indexed by course's name, and each entry is another dictionary.
    # That dictionary is indexed by course's year, and each entry is dictionary with such fields:
    # | field name                       | type   | desc                                                                       |
    # --------------------------------------------------------------------------------------------------------------------------
    # | 'semester'                       | string | course's semester (either z, meaning winter, or l, meaning summer)         |
    # | 'proposal'                       | int    | course's proposal id (see proposal model)                                  |
    # | 'type'                           | string | course's type                                                              |
    # | 'total'                          | int    | number of points gathered by course across all votes in a single year      |
    # | 'count_max'                      | int    | number of votes for this proposal with value = max_vote_value              |
    # | 'votes'                          | int    | number of students that voted for this course                              |
    # | 'teacher'                        | string | lecturer/teacher of this course                                            |
    # | 'enrolled                        | int    | sum of enrolled students. If it's proposal for current year, field is None |
    states_all = SystemState.objects.all().order_by('-year')
    current_year = SystemState.get_current_state().year
    states = []

    for (i, state) in enumerate(states_all):
        if i >= years:
            break
        states.append(state)
    max_vote_value = max(SingleVote.VALUE_CHOICES)[0]

    # Creates set of dictionaries with various data about courses put on the vote.
    # Each dictionary is described by those fields:
    # | field name                       | type   | desc                                                                       |
    # --------------------------------------------------------------------------------------------------------------------------
    # | 'proposal__name'                 | string | course's name                                                              |
    # | 'state__year'                    | string | year in which this instance of the course was put on the vote              |
    # | 'proposal__semester'             | string | course's semester (either z, l, u)                                         |
    # | 'proposal'                       | int    | course's proposal id (see proposal model)                                  |
    # | 'proposal__course_type__name'    | string | course's type                                                              |
    # | 'total'                          | int    | number of points gathered by course across all votes in a single year      |
    # | 'count_max'                      | int    | number of votes for this proposal with value = max_vote_value              |
    # | 'votes'                          | int    | number of students that voted for this course                              |
    # | 'teacher'                        | string | lecturer/teacher of this course                                            |

    votes = SingleVote.objects.filter(
        reduce(lambda x, y: x | y, [Q(state__year=year.year) for year in states]), value__gt=0).values(
            'proposal__name', 'state__year', 'proposal__semester', 'proposal', 'proposal__course_type__name').annotate(
                total=Sum('value'), count_max=Count('value', filter=Q(value=max_vote_value)),
                votes=Count('proposal__name'),
                teacher=Concat('proposal__owner__user__first_name', Value(' '), 'proposal__owner__user__last_name')).order_by('proposal__name', '-state__year')

    courses_data = {}
    # Get rid of courses that existed in previous years, but weren't in this year's vote
    for vote in votes:
        if vote['proposal__name'] not in courses_data:
            if current_year == vote['state__year']:
                courses_data[vote['proposal__name']] = {}
            else:
                continue
        courses_data[vote['proposal__name']][vote['state__year']] = {'total': vote['total'], 'votes': vote['votes'], 'count_max': vote['count_max'],
                                                                     'type': vote['proposal__course_type__name'], 'semester': vote['proposal__semester'],
                                                                     'teacher': vote['teacher'], 'proposal': vote['proposal']}
    # Rearrange data and if course existed in previous years count how many students were enrolled
    for course in courses_data.values():
        for semester, data in course.items():
            instance = CourseInstance.objects.filter(
                offer=data['proposal'], semester__year=semester)
            if not instance:
                data['enrolled'] = None
            else:
                data['enrolled'] = count_students_in_course(instance)
    return courses_data


def count_students_in_groups(groups: List[Group]) -> int:
    # Counts students that were enrolled
    students = Record.objects.filter(
        reduce(lambda x, y: x | y, [Q(group=group)for group in groups]), status=RecordStatus.ENROLLED).distinct().count()
    return students


def count_students_in_course(courses: CourseInstance) -> int:
    enrolled = 0
    for course in courses:
        groups = Group.objects.filter(
            course=course, type=Group.GROUP_TYPE_LECTURE)
        if groups:
            enrolled += count_students_in_groups(groups)
        else:
            groups = Group.objects.filter(course=course)
            enrolled += count_students_in_groups(groups)
    return enrolled


""" Not ready yet
def votes_to_sheets(votes, states):
    scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name(
        'apps/offer/plan/creds.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open('ZapisyTest').sheet1
    sheet.clear()
    row_head = ["Nazwa przedmiotu"]
    row_head2 = ["Głosy", "Głosujący",
                 "Za 3", "Typ", "Semestr", "Wykładowca", "Zapisani", ""]
    for (i, state) in enumerate(states):
        sheet.update_cell(1, i*len(row_head2) + 2, state.year)
        row_head.extend(row_head2)
    sheet.insert_row(row_head, 2)
    row_course = []
    for key, value in votes.items():
        row_course.append(key)
        for state in states:
            year = state.year
            if year in value:
                for k2, v2 in value[year].items():
                    if k2 == 'enrolled':
                        row_course.append(str(value[year][k2]))
                    elif k2 != 'proposal':
                        row_course.append(value[year][k2])
            else:
                row_course.extend(["", "", "", "", "", "", ""])
            row_course.append("")
        del row_course[-1]
    cell_list = sheet.range('A3:X' + str(len(votes)))
    for (i, cell) in enumerate(cell_list):
        cell.value = row_course[i]
    sheet.update_cells(cell_list)
# """
