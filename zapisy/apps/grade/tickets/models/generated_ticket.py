from django.db import models
from django.db.models import Q


class GeneratedTicket(models.Model):
    keys = models.ForeignKey('tickets.RSAKeys', verbose_name='klucz',
                             on_delete=models.CASCADE)
    student = models.ForeignKey('users.Student', verbose_name="student",
                                on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'wygenerowany bilet'
        verbose_name_plural = 'wygenerowane bilety'
        app_label = 'tickets'

    def __str__(self):
        return str(self.student) + " " + str(self.keys)

    @staticmethod
    def student_generated_ticket(poll, student):
        return GeneratedTicket.objects.filter(keys__poll=poll,
                                              student=student).exists()

    @staticmethod
    def student_graded(student, semester):
        return GeneratedTicket.objects.\
                filter(Q(keys__poll_semester=semester) |
                       Q(keys__poll_course__semester=semester) |
                       Q(keys__poll_group__course__semester=semester),
                       student=student).exists()
