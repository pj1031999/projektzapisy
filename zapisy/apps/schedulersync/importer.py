import re
from collections import namedtuple
from datetime import time

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.users.models import Employee
from django.contrib.auth.models import User, Group as AuthGroup
from apps.enrollment.courses.models.classroom import Classroom
from apps.enrollment.courses.models.course import Course, CourseEntity
from apps.enrollment.courses.models.term import Term
from apps.enrollment.courses.models.group import Group
from .models import TermSyncData
from .constants import (
    COURSES_DONT_IMPORT,
    COURSES_MAP,
    GROUP_TYPES,
    LIMITS,
)


Deletion = namedtuple("Deletion", ["term", "group"])
DiffItem = namedtuple("DiffItem", ["field", "val1", "val2"])


class UpdateDiff(list):
    """An intermediate format for storing a difference between updated courses."""
    def __init__(self, term, data):
        super().__init__()
        self.term = term
        self.data = data

    def field(self, field):
        diff = (getattr(self.term, field),
                getattr(self.data, field))
        self.simple(field, *diff)

    def simple(self, field, val1, val2):
        if val1 != val2:
            self.append(DiffItem(field=field, val1=val1, val2=val2))


class ImportedGroup:
    """An intermediate format for storing imported group details"""
    __slots__ = [
        'id', 'entity_name', 'group_type', 'teacher', 'dayOfWeek',
        'start_time', 'end_time', 'classrooms', 'limit'
    ]

    def __init__(self, **names):
        for k, v in names.items():
            setattr(self, k, v)


class ScheduleImporter(BaseCommand):
    """The base class for the command importing schedule.

    It is not a fully-functional class, just all the conversion logic.
    For the command interface, and Scheduler interface, see .management.commands.import_schedule.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # This is only for the tests. Note that all the initialization should get into import_task.
        self.task = None

    def get_entity(self, name):
        """Get a course entity from database by Scheduler-provided course name"""
        name_u = name.upper()
        if name_u in COURSES_DONT_IMPORT:
            return None
        name = COURSES_MAP.get(name_u, name)
        ce = None
        try:
            ce = CourseEntity.objects.get(name_pl__iexact=name)
        except CourseEntity.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f">Couldn't find course entity for {name}")
            )
            if self.prompt("Do you want to create it?"):
                ce = CourseEntity.objects.create(name_pl=name)
        except CourseEntity.MultipleObjectsReturned:
            ces = CourseEntity.objects.filter(name_pl__iexact=name, status=2).order_by('-id')
            if self.verbosity >= 1:
                self.stdout.write(self.style.WARNING("Multiple course entity. Took first among:"))
                for ce in ces:
                    self.stdout.write(self.style.WARNING(f"  {ce!s}"))
                self.stdout.write("")
            ce = ces[0]
        return ce

    def get_course(self, entity, create_courses=False):
        """Get a course from database by its course entity and current semester number
        (possibly creating a new one)."""
        course = None
        try:
            course = Course.objects.get(semester=self.semester, entity=entity)
            self.used_courses.add(course)
        except Course.DoesNotExist:
            if entity.slug is None:
                self.stdout.write(
                    self.style.ERROR(f"Couldn't find slug for {entity}")
                )
            else:
                newslug = f'{entity.slug}_' + re.sub(r'[^\w]', '_', self.semester.get_short_name())
                if create_courses:
                    course = Course(entity=entity, information=entity.information,
                                    semester=self.semester, slug=newslug)
                    course.save()
                    self.created_courses += 1
        return course

    def get_classrooms(self, rooms):
        """Get a list of classroom objects for a list of room numbers."""
        classrooms = []
        for room in rooms:
            room = room.strip()
            try:
                if room:
                    classrooms.append(Classroom.objects.get(number=room))
            except Classroom.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Couldn't find classroom for {room}")
                )
        return classrooms

    def prompt(self, message, choices=("no", "yes")):
        """Ask the interactive user a question with choices provided and return chosen choice's number."""
        if not self.interactive:
            return 0

        self.stdout.write(self.style.WARNING(message))
        for idx, choice in enumerate(choices):
            if idx == 0:
                idx = '(default) 0'
            self.stdout.write(self.style.NOTICE(f"{idx:11}: {choice}"))

        choice = input().strip()
        try:
            choice = int(choice)
            if 0 <= choice < len(choices):
                return choice
        except ValueError:
            pass
        return 0

    def get_employee(self, name):
        """Given an employee identifier from Scheduler (most probably a username),
        find a matching employee from the database (possibly creating one)."""
        details = self.employee_map[name]
        username = details.get('sz_username') or name
        try:
            return Employee.objects.get(user__username=username)
        except Employee.DoesNotExist:
            if not self.interactive:
                details = details.copy()
                del details['terms']
                self.unknown_employees[name] = details
                return self.unknown_employee

        possible = Employee.objects.filter(user__first_name=details['first_name'],
                                           user__last_name=details['last_name'])
        choices = [
            self.unknown_employee,
            "*not listed*",
            "*create a new user (using scheduler-provided data)*"
        ] + list(possible)
        choices_show = [teacher if isinstance(teacher, str) else
                        f"{teacher.user.username} ({teacher})"
                        for teacher in choices]

        user = self.prompt(f"The following teachers were found for {name}"
                           f" ({details['first_name']} {details['last_name']}):", choices_show)

        save_back = False
        if user == 0:  # unknown
            if self.prompt(f"Save back that the teacher is unknown?"):
                save_back = True
        elif user == 1:  # not listed
            while True:
                username = input("Please type the exact username [default: nieznany] ").strip()
                if not username:
                    username = 'nieznany'
                try:
                    possible[user] = Employee.objects.get(user__username=username)
                    break
                except Employee.DoesNotExist:
                    self.stdout.write(self.style.ERROR("No such employee!"))
            save_back = True
        elif user == 2:  # create a new user
            employees, _ = AuthGroup.objects.get_or_create(name='employees')
            user = User.objects.create(
                first_name=details['first_name'], last_name=details['last_name'],
                username=username
            )
            employees.user_set.add(user)
            return Employee.objects.create(user=user)
        else:
            save_back = True

        user = choices[user]
        details['sz_username'] = user.user.username
        if save_back:
            self.save_employee_to_scheduler(details)

        return user

    def save_employee_to_scheduler(self, details):
        pass  # implemented in .management.commands.import_schedule

    def create_or_update_group(self, course, data, create_terms=True):
        """Get a group for the course, and update it according to the data."""
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
            self.stdout.write(
                self.style.SUCCESS(f"Group with scheduler_id={data.id} created!\n"
                                   f"  time: {data.start_time}-{data.end_time}\n"
                                   f"  teacher: {data.teacher}\n"
                                   f"  classrooms: {data.classrooms}\n"))
            self.created_terms += 1
        else:
            for sync_data_object in sync_data_objects:
                term = sync_data_object.term
                diffs = UpdateDiff(term, data)

                diffs.field('dayOfWeek')
                diffs.field('start_time')
                diffs.field('end_time')
                diffs.simple('type', term.group.type, data.group_type)
                diffs.simple('teacher', term.group.teacher, data.teacher)
                term.dayOfWeek = data.dayOfWeek
                term.start_time = data.start_time
                term.end_time = data.end_time
                term.group.type = data.group_type
                term.group.teacher = data.teacher
                old_classrooms = sorted(term.classrooms.all())
                new_classrooms = sorted(data.classrooms)
                if old_classrooms != new_classrooms:
                    diffs.simple('classroom', old_classrooms, new_classrooms)
                    if create_terms:
                        term.classrooms.set(new_classrooms)  # this already saves the relation!
                if diffs:
                    if create_terms:
                        term.save()
                        term.group.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Group {term.group} {term} updated. Difference:"
                        )
                    )
                    for diff in diffs:
                        self.stdout.write(self.style.WARNING(f"  {diff.field}: "), ending="")
                        self.stdout.write(self.style.NOTICE(str(diff.val1)), ending="")
                        self.stdout.write(self.style.WARNING(" -> "), ending="")
                        self.stdout.write(self.style.SUCCESS(str(diff.val2)))
                    self.stdout.write("\n")
                    self.all_updates.append(diffs)
                    self.updated_terms += 1

    def prepare_group(self, g, results, terms):
        """Convert information about group from scheduler format to intermediate format."""
        if g['id'] not in results:
            return None
        group = ImportedGroup(
            id=g['id'],
            entity_name=g['extra']['course'],
            group_type=GROUP_TYPES[g['extra']['group_type']],
            teacher=self.get_employee(g['teachers'][0]),
            limit=g['students_num'],
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
        return group

    def get_groups(self):
        """Get all the groups for the fetched task."""
        results = self.task['timetable']['results']

        groups = []
        terms = {t['id']: t for t in self.assignments['terms']}
        self.employee_map = {}
        for t in self.assignments['teachers']:
            self.employee_map[t['id']] = t
            t.update(t['extra'])
            del t['extra']
        self.employee_map = {t['id']: t for t in self.assignments['teachers']}

        for g in self.assignments['groups']:
            prepared_group = self.prepare_group(g, results, terms)
            if prepared_group is not None:
                groups.append(prepared_group)
            else:
                self.stdout.write(
                    self.style.WARNING(f"Group number {g['id']}"
                                       f" does not have a term ({g['extra']['course']})\n"))
        return groups

    def remove_groups(self):
        """Remove the previously imported groups that were not there in the imported data."""
        groups_to_remove = set()
        sync_data_objects = TermSyncData.objects.filter(term__group__course__semester=self.semester)
        for sync_data_object in sync_data_objects:
            if sync_data_object.scheduler_id not in self.scheduler_ids:
                groups_to_remove.add(sync_data_object.term.group)
                deletion = Deletion(term=str(sync_data_object.term),
                                    group=str(sync_data_object.term.group))
                self.stdout.write(
                    self.style.NOTICE(
                        f"Term {deletion.term} for group {deletion.group} removed\n"))
                self.all_deletions.append(deletion)
                if self.delete_groups:
                    sync_data_object.term.delete()
                    sync_data_object.delete()
        for group in groups_to_remove:
            if not Term.objects.filter(group=group):
                if self.delete_groups:
                    group.delete()

    @transaction.atomic
    def import_task(self, create_courses=False, create_terms=True):
        """Perform an import from Scheduler.

        This is where all the per-import initialization takes place.
        It imports a task that was previously fetched using
        class fields `task` and `assignments`."""
        self.created_terms = 0
        self.updated_terms = 0
        self.created_courses = 0
        self.all_updates = []
        self.all_creations = []
        self.all_deletions = []
        self.used_courses = set()
        self.scheduler_ids = set()
        self.unknown_employees = {}
        self.unknown_employee = Employee.objects.get(user__username='nieznany')
        for g in self.get_groups():
            self.scheduler_ids.add(int(g.id))
            entity = self.get_entity(g.entity_name)
            if entity is not None:
                course = self.get_course(entity, create_courses)
                if course is None:
                    self.stdout.write(self.style.WARNING(f"Course {entity} does not exist!"))
                else:
                    self.create_or_update_group(course, g, create_terms)
        self.remove_groups()
        self.stdout.write(
            self.style.SUCCESS(f"Created {self.created_courses} courses successfully! "
                               f"Moreover {len(self.used_courses)} courses were already there."))
        self.stdout.write(
            self.style.SUCCESS(f"Created {self.created_terms} terms "
                               f"and updated {self.updated_terms} terms successfully!"))
        if self.unknown_employees:
            self.stdout.write(
                self.style.SUCCESS(f"These employees were not found: {self.unknown_employees}"))

    def prepare_slack_message(self):
        """After a successful import, prepare a summary of changes to display on Slack."""
        attachments = []
        for term in self.all_creations:
            text = (f"day: {term.dayOfWeek}\nstart_time: {term.start_time}\n"
                    f"end_time: {term.end_time}\nteacher: {term.group.teacher}")
            attachment = {
                'color': 'good',
                'title': f"Created: {term.group}",
                'text': text
            }
            attachments.append(attachment)
        for diffs in self.all_updates:
            text = ""
            for diff in diffs:
                text += f"{diff.field}: {diff.val1}->{diff.val2}\n"
            attachment = {
                'color': 'warning',
                'title': f"Updated: {diffs.term.group}",
                'text': text
            }
            attachments.append(attachment)
        for deletion in self.all_deletions:
            attachment = {
                'color': 'danger',
                'title': "Deleted a term:",
                'text': f"group: {deletion.group}\nterm: {deletion.term}"
            }
            attachments.append(attachment)
        return attachments
