from django.db import models
from choicesenum import ChoicesEnum

from apps.users.models import Employee, Student

MAX_THESIS_TITLE_LENGTH = 300

class ThesisType(ChoicesEnum):
    MASTERS = 0, "mgr"
    ENGINEERS = 1, "inż"
    BACHELORS = 2, "lic"
    ISIM = 3, "isim"
    BACHELORS_ENGINEERS = 4, "lic+inż"
    BACHELORS_ENGINEERS_ISIM = 5, "lic+inż+isim"

class ThesisStatus(ChoicesEnum):
    BEING_EVALUATED = 1, "weryfikowana przez komisję"
    RETURNED_FOR_CORRECTIONS = 2, "zwrócona do poprawek"
    ACCEPTED = 3, "zaakceptowana"
    IN_PROGRESS = 4, "w realizacji"
    DEFENDED = 5, "obroniona"

class Thesis(models.Model):
    """
    Model used to represent thesis in database.
    """

    date_added = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now_add=True)
    title = models.TextField(max_length=MAX_THESIS_TITLE_LENGTH)
    status = models.SmallIntegerField(choices=ThesisStatus.choices())
    type = models.SmallIntegerField(choices=ThesisType.choices())
    description = models.TextField(blank=True)
    advisor = models.ForeignKey(Employee,
                                on_delete=models.PROTECT,
                                null=True,
                                blank=True,
                                related_name='thesis_advisor')
    supporting_advisor = models.ForeignKey(Employee,
                                           on_delete=models.PROTECT,
                                           null=True,
                                           blank=True,
                                           related_name='thesis_supporting_advisor')
    students = models.ManyToManyField(Student,
                                      blank=True)


