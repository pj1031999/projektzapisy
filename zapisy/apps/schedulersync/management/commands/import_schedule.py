import requests

from django.conf import settings
from apps.enrollment.courses.models.semester import Semester
from ...importer import ScheduleImporter
from ...constants import (
    SLACK_WEBHOOK_URL,
    URL_CONFIG,
    URL_LOGIN,
)


class Command(ScheduleImporter):
    help = "Imports the timetable for the next semester from the external scheduler."

    def add_arguments(self, parser):
        parser.add_argument('url_schedule', help="(task url) Should look like this: "
                            '/scheduler/api/task/07164b02-de37-4ddc-b81b-ddedab533fec/')
        parser.add_argument('--semester', type=int, default=0)
        parser.add_argument('--create-courses', action='store_true')
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--slack', action='store_true', dest='write_to_slack')
        parser.add_argument('--delete-groups', action='store_true')
        parser.add_argument('--interactive', action='store_true')

    def get_task(self):
        """Fetch a task from Scheduler and return it, setting up a session."""
        self.client = requests.session()
        self.client.get(URL_LOGIN)
        csrftoken = self.client.cookies['csrftoken']
        secrets_env = settings.env
        scheduler_username = secrets_env.str('SCHEDULER_USERNAME')
        scheduler_password = secrets_env.str('SCHEDULER_PASSWORD')
        login_data = {'username': scheduler_username, 'password': scheduler_password,
                      'csrfmiddlewaretoken': csrftoken, 'next': self.url_schedule}

        # the first request is redirected through the login page
        req1 = self.client.post(URL_LOGIN, data=login_data)
        task = req1.json()

        # and the second one goes directly
        self.url_assignments = URL_CONFIG.format(id=task['config_id'])
        req2 = self.client.get(self.url_assignments)
        self.assignments = req2.json()

        return task

    def save_back(self, details):
        """Save employee details back to Scheduler (used in interactive mode)."""
        response = self.client.post(self.url_assignments + 'add/', json={
            'config_id': self.assignments['id'],
            'type': 'teacher',
            'mode': 'edit',
            'teacher': details
        }, headers={'X-CSRFToken': self.client.cookies['csrftoken']})

        if response.status_code != 200:
            raise ValueError(
                f"Request to scheduler returned an error {response.status_code}, "
                f"the response is:\n{response.text[:10000]}"
            )

    def write_to_slack(self):
        """Write a summary of changes to Slack."""
        attachments = self.prepare_slack_message()
        if attachments:
            text = "The following groups were updated in fereol (scheduler's sync):"
        else:
            text = "No groups were updated in fereol (scheduler's sync)."
        slack_data = {
            'text': text,
            'attachments': attachments
        }
        response = requests.post(SLACK_WEBHOOK_URL, json=slack_data)
        if response.status_code != 200:
            raise ValueError(
                f"Request to slack returned an error {response.status_code}, the response is:\n{response.text}"
            )

    def handle(self, *,
               dry_run=False, write_to_slack=False, delete_groups=False,
               verbosity=0, url_schedule=None,
               semester=0, create_courses=False, interactive=False,
               task_data=None,
               **options):
        self.semester = (Semester.objects.get_next() if semester == 0
                         else Semester.objects.get(pk=semester))
        self.url_schedule = url_schedule
        self.verbosity = verbosity
        self.interactive = interactive
        self.delete_groups = delete_groups
        if self.verbosity >= 1:
            self.stdout.write(f"Adding to semester: {self.semester}\n")
        if not task_data:
            task_data = self.get_task()

        if dry_run:
            if self.verbosity >= 1:
                self.stdout.write("Dry run is on. Nothing will be saved.")
            self.import_from_api(False, False, task=task_data)
        else:
            self.import_from_api(create_courses, task=task_data)
        if write_to_slack:
            self.write_to_slack()
