from django.db import models


class GeneratedTicket(models.Model):
    keys = models.ForeignKey('tickets.RSAKeys', verbose_name='ankieta',
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
