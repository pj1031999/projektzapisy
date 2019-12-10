from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from datetime import datetime, timedelta
from apps.users.models import Student, Employee
from apps.theses.enums import ThesisKind, ThesisStatus
from datetime import date
from apps.theses.users import is_theses_board_member

MAX_THESIS_TITLE_LEN = 300
MAX_REJECTION_REASON_LENGTH = 500


class Remark(models.Model):
    author = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="remark_author")
    text = models.TextField(blank=True)


class Thesis(models.Model):
    """
        Thesis model
    """
    #objects = models.Manager()
    #rest_objects = APIManager()

    #def __init__(self, *args, **kwargs):
     #   super().__init__(*args, **kwargs)
        # Save the status so that, when saving, we can determine whether or not it changed
        # See https://stackoverflow.com/a/1793323
        # If pk is None, we are creating this model, so don't save the status
        #self.__original_status = self.status if self.pk is not None else None
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=MAX_THESIS_TITLE_LEN, unique=True)
    # the related_name's below are necessary because we have multiple foreign keys pointing
    # to the same model and Django isn't smart enough to generate unique reverse accessors
    advisor = models.ForeignKey(
        Employee, on_delete=models.PROTECT, blank=True, null=True,
        related_name='thesis_advisor'
    )
    supporting_advisor = models.ForeignKey(
        Employee, on_delete=models.PROTECT, blank=True, null=True,
        related_name='thesis_supporting_advisor'
    )
    kind = models.SmallIntegerField(choices=ThesisKind.choices())
    status = models.SmallIntegerField(choices=ThesisStatus.choices())
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
    # models.ManyToManyField(Remark, verbose_name=("rejection_reasons"))
    rejection_reasons = models.ManyToManyField(Remark, blank=True)

    class Meta:
        verbose_name = "praca dyplomowa"
        verbose_name_plural = "prace dyplomowe"

    def get_kind_display(self):
        return ThesisKind(self.kind).display

    def get_status_display(self):
        return ThesisStatus(self.status).display

    def can_see_thesis(self, user):
        return ((self.status != ThesisStatus.BEING_EVALUATED and self.status != ThesisStatus.RETURNED_FOR_CORRECTIONS)
        or is_theses_board_member(user)
        or user == (self.advisor.user if self.advisor != None else None)
        or user == (self.supporting_advisor.user if self.supporting_advisor != None else None)
        or user.is_staff)

    @property
    def is_reserved(self):
        return self.reserved_until and date.today() <= self.reserved_until

    @property
    def has_been_accepted(self):
        return self.status != ThesisStatus.RETURNED_FOR_CORRECTIONS and self.status != ThesisStatus.BEING_EVALUATED
