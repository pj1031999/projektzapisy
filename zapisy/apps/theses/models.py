from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from apps.theses.enums import ThesisKind, ThesisStatus, ThesisVote
from apps.theses.users import is_theses_board_member
from apps.theses.validators import validate_master_rejecter, validate_num_required_votes
from apps.users.models import Employee, Student

MAX_THESIS_TITLE_LEN = 300
MAX_REJECTION_REASON_LENGTH = 500
MAX_ASSIGNED_STUDENTS = 2


class ThesesSystemSettings(models.Model):
    num_required_votes = models.SmallIntegerField(
        verbose_name="Liczba głosów wymaganych do zaakceptowania",
        validators=[validate_num_required_votes]
    )
    master_rejecter = models.ForeignKey(
        Employee, null=True, on_delete=models.PROTECT,
        verbose_name="Członek komisji odpowiedzialny za zwracanie prac do poprawek",
        validators=[validate_master_rejecter]
    )

    def __str__(self):
        return "Ustawienia systemu"

    class Meta:
        verbose_name = "ustawienia systemu prac dyplomowych"
        verbose_name_plural = "ustawienia systemu prac dyplomowych"


class Vote(models.Model):
    owner = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="vote_owner")
    vote = models.SmallIntegerField(choices=ThesisVote.choices())

    class Meta:
        verbose_name = "głos"
        verbose_name_plural = "głosy"


class Remark(models.Model):
    modified = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="remark_author")
    text = models.TextField(blank=True)

    class Meta:
        verbose_name = "uwaga"
        verbose_name_plural = "uwagi"


class Thesis(models.Model):
    """
        Thesis model
    """
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=MAX_THESIS_TITLE_LEN, unique=True)

    advisor = models.ForeignKey(
        Employee, on_delete=models.PROTECT, blank=True, null=True,
        related_name='thesis_advisor'
    )
    supporting_advisor = models.ForeignKey(
        Employee, on_delete=models.PROTECT, blank=True, null=True,
        related_name='thesis_supporting_advisor'
    )
    kind = models.SmallIntegerField(choices=ThesisKind.choices())
    status = models.SmallIntegerField(
        choices=ThesisStatus.choices(), blank=True, null=True)
    # How long the assigned student(s) has/have to complete their work on this thesis
    # Note that this is only a convenience field for the users, the system
    # does not enforce this in any way
    reserved_until = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True)
    students = models.ManyToManyField(Student, blank=True)
    added = models.DateTimeField(auto_now_add=True)
    # A thesis is _modified_ when its status changes
    modified = models.DateTimeField(auto_now_add=True)

    # The "official" rejection reason, filled out by board member
    remarks = models.ManyToManyField(Remark, blank=True)

    votes = models.ManyToManyField(Vote, blank=True)

    class Meta:
        verbose_name = "praca dyplomowa"
        verbose_name_plural = "prace dyplomowe"

    def delete(self, *args, **kwargs):
        self.remarks.all().delete()
        self.votes.all().delete()
        super().delete(*args, **kwargs)

    def get_kind_display(self):
        return ThesisKind(self.kind).display

    def get_status_display(self):
        return ThesisStatus(self.status).display

    def can_see_thesis(self, user):
        return ((self.status != ThesisStatus.BEING_EVALUATED and self.status != ThesisStatus.RETURNED_FOR_CORRECTIONS) or
                is_theses_board_member(user) or
                (self.advisor is not None and user == self.advisor.user) or
                (self.supporting_advisor is not None and user == self.supporting_advisor.user) or
                user.is_staff)

    def get_accepted_votes(self):
        return len(self.votes.filter(vote=ThesisVote.ACCEPTED))

    def is_mine(self, user):
        return self.advisor is not None and user == self.advisor.user

    def is_student_assigned(self, user):
        return self.students is not None and self.students.filter(user=user).exists()

    def is_supporting_advisor_assigned(self, user):
        return self.supporting_advisor is not None and user == self.supporting_advisor.user

    @property
    def is_reserved(self):
        return self.reserved_until and date.today() <= self.reserved_until

    @property
    def has_been_accepted(self):
        return self.status != ThesisStatus.RETURNED_FOR_CORRECTIONS and self.status != ThesisStatus.BEING_EVALUATED
