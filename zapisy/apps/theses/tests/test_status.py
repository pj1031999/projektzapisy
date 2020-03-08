from django.test import TestCase
from apps.theses.models import Thesis, Vote, ThesesSystemSettings
from apps.theses.enums import ThesisStatus, ThesisVote
from apps.theses.system_settings import change_status
from apps.theses.forms import EditThesisForm
from apps.users.models import Employee, Student, User
from apps.users.tests.factories import EmployeeFactory, StudentFactory, UserFactory


class ThesisStatusChangeTestCase(TestCase):
    def setUp(self):
        self.thesis_owner = EmployeeFactory()
        self.student = StudentFactory()

        Thesis.objects.create(title="NoStudents",
                              advisor=self.thesis_owner, kind=0, status=ThesisStatus.BEING_EVALUATED)

        Thesis.objects.create(title="NoStudentsEdit",
                              advisor=self.thesis_owner, kind=0, status=ThesisStatus.ACCEPTED)

        thesis_with_students = Thesis.objects.create(
            title="WithStudents", advisor=self.thesis_owner, kind=0, status=ThesisStatus.BEING_EVALUATED)
        thesis_with_students.students.add(self.student)

        settings = ThesesSystemSettings.objects.get()
        settings.num_required_votes = 1
        settings.save()

    def test_vote(self):
        thesis_no_students = Thesis.objects.get(title="NoStudents")
        thesis_with_students = Thesis.objects.get(title="WithStudents")

        vote_no_students = Vote.objects.create(owner=EmployeeFactory(),
                                               vote=ThesisVote.ACCEPTED, thesis=thesis_no_students)
        vote_with_students = Vote.objects.create(owner=EmployeeFactory(),
                                                 vote=ThesisVote.ACCEPTED, thesis=thesis_with_students)

        change_status(thesis_no_students, vote_no_students.vote)
        change_status(thesis_with_students, vote_with_students.vote)

        self.assertEqual(thesis_no_students.status, ThesisStatus.ACCEPTED)
        self.assertEqual(thesis_with_students.status, ThesisStatus.IN_PROGRESS)

    def test_edit(self):
        thesis = Thesis.objects.get(title="NoStudentsEdit")
        id = thesis.id

        self.client.force_login(self.thesis_owner.user)

        response = self.client.post('/theses/' + str(id) + '/edit',
                                    {'title': thesis.title, 'advisor': thesis.advisor, 'supporting_advisor': thesis.supporting_advisor, 'reserved_until': thesis.reserved_until, 'kind': thesis.kind, 'status': thesis.status, 'description': thesis.description})
        self.assertEqual(thesis.status,
                         ThesisStatus.IN_PROGRESS.value)
