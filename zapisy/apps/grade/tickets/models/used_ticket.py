from django.db import models


class UsedTicked(models.Model):
    poll = models.ForeignKey('poll.Poll', verbose_name='ankieta',
                             on_delete=models.CASCADE)
    student = models.ForeignKey('student.Student', verbose_name="student",
                                on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'wykorzystany bilet'
        verbose_name_plural = 'wykorzystane bilety'
        app_label = 'tickets'

    def __str__(self):
        return str(self.student) + " " + str(self.poll)
