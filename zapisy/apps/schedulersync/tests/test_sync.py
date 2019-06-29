import copy
import json
import os

from django.test import TestCase, override_settings

from apps.users.models import Employee
from apps.enrollment.courses.models.course import Course
from apps.enrollment.courses.models.group import Group
from apps.enrollment.courses.tests.factories import ClassroomFactory, SemesterFactory
from apps.users.tests.factories import UserFactory, EmployeeFactory

from ..management.commands.import_schedule import Command as ImportCommand


def fake_prompt(message, choices=("no", "yes")):
    return len(choices) - 1


class StdoutSuppressor:
    def __init__(self, test):
        self.cmd = test.cmd
        self.save_stdout = self.cmd.stdout

    def write(self, *args, **kw):
        pass

    def __enter__(self):
        self.cmd.stdout = self

    def __exit__(self, val, tp, tb):
        self.cmd.stdout = self.save_stdout


# When saving modified groups, the queues move.
# The tests can be run without Redis, and asynchronous queues may require that.
@override_settings(RUN_ASYNC=False)
class Test(TestCase):
    """Testy do importu danych ze Schedulera.
    """

    @classmethod
    def setUpTestData(cls):
        cls.cmd = cmd = ImportCommand()
        cmd.prompt = fake_prompt
        cmd.save_back = None

        files = 'sample-config.json', 'sample-config2.json', 'sample-task.json', 'sample-task2.json'
        objects = []
        for name in files:
            with open(os.path.join(os.path.dirname(__file__), name)) as fp:
                objects.append(json.load(fp))

        cls.assignments = objects[0]
        cls.assignments2 = objects[1]
        cls.task1 = objects[2]
        cls.task2 = objects[3]
        EmployeeFactory(user=UserFactory(username='nieznany', first_name="Nieznany", last_name="Prowadzący"))
        ClassroomFactory(number="5")
        ClassroomFactory(number="103")
        ClassroomFactory(number="105")
        ClassroomFactory(number="108")
        ClassroomFactory(number="141")
        SemesterFactory()

    def test_creation(self):
        self.cmd.assignments = copy.deepcopy(self.assignments)
        with StdoutSuppressor(self):
            # interactive=True, but cmd.prompt == fake_prompt
            self.cmd.handle(task_data=self.task1, create_courses=True, interactive=True)

        self.assertEqual(Employee.objects.get(user__username='teach1').user.last_name, 'Pierwszy')
        self.assertEqual(Employee.objects.get(user__username='teach2').user.last_name, 'Drugi')
        self.assertEqual(Group.objects.get(course__entity__name_pl='Myślenie').course.entity.name_pl, 'Myślenie')

    def test_removal(self):
        self.test_creation()

        try:
            self.cmd.assignments = copy.deepcopy(self.assignments2)
            with StdoutSuppressor(self):
                self.cmd.handle(task_data=self.task2, delete_groups=True)
            self.assertRaises(Group.DoesNotExist, Group.objects.get, course__entity__name_pl='Myślenie')
        finally:
            Course.objects.get(entity__name_pl='Myślenie').delete()
