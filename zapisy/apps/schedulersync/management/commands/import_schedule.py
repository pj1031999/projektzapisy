import re
from datetime import time
import os

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

import environ
import requests

from apps.users.models import Employee
from apps.enrollment.courses.models.classroom import Classroom
from apps.enrollment.courses.models.course import Course, CourseEntity
from apps.enrollment.courses.models.semester import Semester
from apps.enrollment.courses.models.term import Term
from apps.enrollment.courses.models.group import Group
from apps.schedulersync.models import TermSyncData

SCHEDULER_BASE = 'http://scheduler.gtch.eu'

URL_LOGIN = SCHEDULER_BASE + '/admin/login/'

SLACK_WEBHOOK_URL = (
    'https://hooks.slack.com/services/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'
)

# The mapping between group types in scheduler and enrollment system
# w (wykład), p (pracownia), c (ćwiczenia), s (seminarium), r (ćwiczenio-pracownia),
# e (repetytorium), o (projekt)
GROUP_TYPES = {'w': '1', 'e': '9', 'c': '2', 'p': '3',
               'r': '5', 's': '6', 'o': '10'}

# The default limits for group types
LIMITS = {'1': 300, '9': 300, '2': 20, '3': 15, '5': 18, '6': 15, '10': 15}

COURSES_MAP = {
    'PRAKTYKA ZAWODOWA - 3 TYGODNIE': 'PRAKTYKA ZAWODOWA - TRZY TYGODNIE',
    'PRAKTYKA ZAWODOWA - 4 TYGODNIE': 'PRAKTYKA ZAWODOWA - CZTERY TYGODNIE',
    'PRAKTYKA ZAWODOWA - 5 TYGODNI': 'PRAKTYKA ZAWODOWA - PIĘĆ TYGODNI',
    'PRAKTYKA ZAWODOWA - 6 TYGODNI': 'PRAKTYKA ZAWODOWA - SZEŚĆ TYGODNI'
}

COURSES_DONT_IMPORT = [
    'ALGEBRA I',
    'ALGEBRA LINIOWA 2',
    'ALGEBRA LINIOWA 2R',
    'ANALIZA MATEMATYCZNA II',
    'FUNKCJE ANALITYCZNE 1',
    'RÓWNANIA RÓŻNICZKOWE 1',
    'RÓWNANIA RÓŻNICZKOWE 1R',
    'TEORIA PRAWDOPODOBIEŃSTWA 1',
    'TOPOLOGIA']


class ImportedGroup:
    __slots__ = [
        'id', 'entity_name', 'group_type', 'teacher', 'dayOfWeek',
        'start_time', 'end_time', 'classrooms', 'limit'
    ]

    def __init__(self, **names):
        for k, v in names.items():
            setattr(self, k, v)


class Command(BaseCommand):
    help = "Imports the timetable for the next semester from the external scheduler."

    def add_arguments(self, parser):
        parser.add_argument('url_assignments', help="(config url) Should look like this: "
                            '/scheduler/api/config/2017-18-lato3-2/')
        parser.add_argument('url_schedule', help="(task url) Should look like this: "
                            '/scheduler/api/task/07164b02-de37-4ddc-b81b-ddedab533fec/')
        parser.add_argument('--semester', type=int, default=0)
        parser.add_argument('--create-courses', action='store_true')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--slack', action='store_true', dest='write_to_slack')
        parser.add_argument('--delete-groups', action='store_true')

    def get_entity(self, name):
        name = name.upper()
        if name in COURSES_MAP:
            name = COURSES_MAP[name]
        if name in COURSES_DONT_IMPORT:
            return None
        ce = None
        try:
            ce = CourseEntity.objects.get(name_pl__iexact=name)
        except CourseEntity.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(">Couldn't find course entity for {}".format(name))
            )
        except CourseEntity.MultipleObjectsReturned:
            ces = CourseEntity.objects.filter(name_pl__iexact=name, status=2).order_by('-id')
            if self.verbosity >= 1:
                self.stdout.write(self.style.WARNING("Multiple course entity. Took first among:"))
                for ce in ces:
                    self.stdout.write(self.style.WARNING("  {}".format(str(ce))))
                self.stdout.write("")
            ce = ces[0]
        return ce

    def get_course(self, entity, create_courses=False):
        course = None
        try:
            course = Course.objects.get(semester=self.semester, entity=entity)
            self.used_courses.add(course)
        except Course.DoesNotExist:
            if entity.slug is None:
                self.stdout.write(
                    self.style.ERROR("Couldn't find slug for {}".format(entity))
                )
            else:
                newslug = '{}_{}'.format(entity.slug,
                                         re.sub(r'[^\w]', '_', self.semester.get_short_name()))
                if create_courses:
                    course = Course(entity=entity, information=entity.information,
                                    semester=self.semester, slug=newslug)
                    course.save()
                    self.created_courses += 1
        return course

    def get_classrooms(self, rooms):
        classrooms = []
        for room in rooms:
            room = room.strip()
            try:
                if room:
                    classrooms.append(Classroom.objects.get(number=room))
            except Classroom.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR("Couldn't find classroom for {}".format(room))
                )
        return classrooms

    def get_employee(self, name):
        details = self.employee_map[name]
        username = details.get('sz_username') or name
        try:
            return Employee.objects.get(user__username=username)
        except Employee.DoesNotExist:
            possible = Employee.objects.filter(user__first_name=details['first_name'],
                                               user__last_name=details['last_name'])
            if len(possible) == 1:
                details['sz_username'] = possible[0].user.username
            self.unknown_employees[name] = details
            return Employee.objects.get(user__username='nieznany')

    def create_or_update_group(self, course, data, create_terms=True):
        sync_data_objects = TermSyncData.objects.filter(
            scheduler_id=data.id, term__group__course__semester=self.semester).select_related(
                'term', 'term__group').prefetch_related('term__classrooms')
        sync_data_objects = list(sync_data_objects)
        if not sync_data_objects:
            if create_terms:
                # Create the group in the enrollment system
                if data.group_type == '1':
                    # The lecture always has a single group but possibly many terms
                    group, _ = Group.objects.get_or_create(course=course,
                                                           teacher=data.teacher,
                                                           type=data.group_type,
                                                           limit=data.limit)
                else:
                    group = Group.objects.create(course=course,
                                                 teacher=data.teacher,
                                                 type=data.group_type,
                                                 limit=data.limit)
                term = Term.objects.create(dayOfWeek=data.dayOfWeek,
                                           start_time=data.start_time,
                                           end_time=data.end_time,
                                           group=group)
                term.classrooms.set(data.classrooms)
                term.save()
                self.all_creations.append(term)
                TermSyncData.objects.create(term=term, scheduler_id=data.id)
            self.stdout.write(self.style.SUCCESS("Group with scheduler_id={} created!"
                                                 .format(data.id)))
            self.stdout.write(self.style.SUCCESS("  time: {}-{}"
                                                 .format(data.start_time, data.end_time)))
            self.stdout.write(self.style.SUCCESS("  teacher: {}"
                                                 .format(data.teacher)))
            self.stdout.write(self.style.SUCCESS("  classrooms: {}\n"
                                                 .format(data.classrooms)))
            self.created_terms += 1
        else:
            for sync_data_object in sync_data_objects:
                term = sync_data_object.term
                diff_track_fields = ['dayOfWeek', 'start_time', 'end_time']
                diffs = []
                for field in diff_track_fields:
                    diff = tuple(getattr(obj, field) for obj in (term, data))
                    if diff[0] != diff[1]:
                        diffs.append((field, diff))
                if term.group.type != data.group_type:
                    diffs.append(('type', (term.group.type, data.group_type)))
                if term.group.teacher != data.teacher:
                    diffs.append(('teacher', (term.group.teacher, data.teacher)))
                term.dayOfWeek = data.dayOfWeek
                term.start_time = data.start_time
                term.end_time = data.end_time
                term.group.type = data.group_type
                term.group.teacher = data.teacher
                old_classrooms = set(term.classrooms.all())
                if old_classrooms != set(data.classrooms):
                    diffs.append(('classroom', (list(old_classrooms),
                                                data.classrooms)))
                    if create_terms:
                        term.classrooms.set(data.classrooms)  # this already saves the relation!
                if diffs:
                    if create_terms:
                        term.save()
                        term.group.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            "Group {} {} updated. Difference:".format(term.group, term)
                        )
                    )
                    for diff in diffs:
                        self.stdout.write(self.style.WARNING("  {}: ".format(diff[0])), ending="")
                        self.stdout.write(self.style.NOTICE(str(diff[1][0])), ending="")
                        self.stdout.write(self.style.WARNING(" -> "), ending="")
                        self.stdout.write(self.style.SUCCESS(str(diff[1][1])))
                    self.stdout.write("\n")
                    self.all_updates.append((term, diffs))
                    self.updated_terms += 1

    def prepare_group(self, g, results, terms):
        """Convert information about group from scheduler format."""
        if g['id'] not in results:
            return None
        group = ImportedGroup(
            id=g['id'],
            entity_name=g['extra']['course'],
            group_type=GROUP_TYPES[g['extra']['group_type']],
            teacher=self.get_employee(g['teachers'][0])
        )

        # start_time will be determined as the minimum start_time among all terms
        # end_time - as maximum. All the terms in scheduler are one hour long.
        start_time = 24  # acts as inifinity
        end_time = 0
        classrooms = set()
        for entry in results[g['id']]:
            term = terms[entry['term']]

            t_start = term['start']['hour']
            t_end = term['end']['hour']
            if t_start < start_time:
                start_time = t_start
            if t_end > end_time:
                end_time = t_end
            group.dayOfWeek = str(term['day'] + 1)
            classrooms.add(entry['room'])
        group.start_time = time(hour=start_time)
        group.end_time = time(hour=end_time)
        group.classrooms = self.get_classrooms(classrooms)
        group.limit = LIMITS[group.group_type]
        return group

    def get_groups(self):
        client = requests.session()
        client.get(URL_LOGIN)
        csrftoken = client.cookies['csrftoken']
        secrets_env = self.get_secrets_env()
        scheduler_username = secrets_env.str('SCHEDULER_USERNAME')
        scheduler_password = secrets_env.str('SCHEDULER_PASSWORD')
        login_data = {'username': scheduler_username, 'password': scheduler_password,
                      'csrfmiddlewaretoken': csrftoken, 'next': self.url_assignments}

        # the first request is redirected through the login page
        req1 = client.post(URL_LOGIN, data=login_data)
        assignments = req1.json()

        # and the second one goes directly
        req2 = client.get(SCHEDULER_BASE + self.url_schedule)
        results = req2.json()['timetable']['results']

        groups = []
        terms = {t['id']: t for t in assignments['terms']}
        self.employee_map = {t['id']: t['extra'] for t in assignments['teachers']}

        for g in assignments['groups']:
            prepared_group = self.prepare_group(g, results, terms)
            if prepared_group is not None:
                groups.append(prepared_group)
            else:
                self.stdout.write(self.style.WARNING("Group number {} does not have a term ({})\n"
                                                     .format(g['id'], g['extra']['course'])))
        return groups

    def remove_groups(self):
        groups_to_remove = set()
        sync_data_objects = TermSyncData.objects.filter(term__group__course__semester=self.semester)
        for sync_data_object in sync_data_objects:
            if sync_data_object.scheduler_id not in self.scheduler_ids:
                groups_to_remove.add(sync_data_object.term.group)
                self.stdout.write(
                    self.style.NOTICE(
                        "Term {} for group {} removed\n".format(
                            sync_data_object.term,
                            sync_data_object.term.group)))
                self.all_deletions.append((str(sync_data_object.term),
                                           str(sync_data_object.term.group)))
                if self.delete_groups:
                    sync_data_object.term.delete()
                    sync_data_object.delete()
        for group in groups_to_remove:
            if not Term.objects.filter(group=group):
                if self.delete_groups:
                    group.delete()

    @transaction.atomic
    def import_from_api(self, create_courses=False, create_terms=True):
        self.created_terms = 0
        self.updated_terms = 0
        self.created_courses = 0
        self.all_updates = []
        self.all_creations = []
        self.all_deletions = []
        self.used_courses = set()
        self.scheduler_ids = set()
        self.unknown_employees = {}
        groups = self.get_groups()
        for g in groups:
            self.scheduler_ids.add(int(g.id))
            entity = self.get_entity(g.entity_name)
            if entity is not None:
                course = self.get_course(entity, create_courses)
                if course is None:
                    raise CommandError("Course {} does not exist! Check your input file."
                                       .format(entity))
                self.create_or_update_group(course, g, create_terms)
        self.remove_groups()
        self.stdout.write(self.style.SUCCESS("Created {} courses successfully! "
                                             "Moreover {} courses were already there."
                                             .format(self.created_courses, len(self.used_courses))))
        self.stdout.write(self.style.SUCCESS("Created {} terms and updated {} terms successfully!"
                                             .format(self.created_terms, self.updated_terms)))
        if self.unknown_employees:
            self.stdout.write(self.style.SUCCESS("These employees were not found: {}"
                                                 .format(self.unknown_employees)))

    def prepare_slack_message(self):
        attachments = []
        for term in self.all_creations:
            text = "day: {}\nstart_time: {}\nend_time: {}\nteacher: {}".format(
                term.dayOfWeek, term.start_time, term.end_time, term.group.teacher
            )
            attachment = {
                'color': 'good',
                'title': "Created: {}".format(term.group),
                'text': text
            }
            attachments.append(attachment)
        for term, diffs in self.all_updates:
            text = ""
            for diff in diffs:
                text = text + "{}: {}->{}\n".format(diff[0], diff[1][0], diff[1][1])
            attachment = {
                'color': 'warning',
                'title': "Updated: {}".format(term.group),
                'text': text
            }
            attachments.append(attachment)
        for term_str, group_str in self.all_deletions:
            attachment = {
                'color': 'danger',
                'title': "Deleted a term:",
                'text': "group: {}\nterm: {}".format(group_str, term_str)
            }
            attachments.append(attachment)
        return attachments

    def write_to_slack(self):
        slack_data = {
            'text': "The following groups were updated in fereol (scheduler's sync):",
            'attachments': self.prepare_slack_message()
        }
        response = requests.post(SLACK_WEBHOOK_URL, json=slack_data)
        if response.status_code != 200:
            raise ValueError(
                "Request to slack returned an error %s, the response is:\n%s"
                % (response.status_code, response.text)
            )

    def get_secrets_env(self):
        env = environ.Env()
        BASE_DIR = os.path.abspath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            *[os.pardir] * 4))
        self.stdout.write(os.path.join(BASE_DIR, os.pardir, 'env', '.env'))
        environ.Env.read_env(os.path.join(BASE_DIR, os.pardir, 'env', '.env'))
        return env

    def handle(self, *args,
               dry_run=False, write_to_slack=False, delete_groups=False,
               verbosity=None, url_schedule=None, url_assignments=None,
               semester=0, create_courses=False,
               **options):
        self.semester = (Semester.objects.get_next() if semester == 0
                         else Semester.objects.get(pk=semester))
        self.url_assignments = url_assignments
        self.url_schedule = url_schedule
        self.verbosity = verbosity
        if self.verbosity >= 1:
            self.stdout.write("Adding to semester: {}\n".format(self.semester))
        self.delete_groups = delete_groups
        if dry_run:
            if self.verbosity >= 1:
                self.stdout.write("Dry run is on. Nothing will be saved.")
            self.import_from_api(False, False)
        else:
            self.import_from_api(create_courses)
        if write_to_slack:
            self.write_to_slack()
