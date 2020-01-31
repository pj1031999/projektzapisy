from django.db import models


class UsedTicket(models.Model):
    poll = models.ForeignKey("poll.Poll",
                             verbose_name=("ankieta"),
                             on_delete=models.CASCADE)
    ticket = models.TextField(verbose_name='bilet')
    signed_ticket = models.TextField(verbose_name='podpisany bilet')

    class Meta:
        verbose_name = 'wykorzystany bilet'
        verbose_name_plural = 'wykorzystane bilety'
        app_label = 'tickets'

    def __str__(self):
        return str(self.student) + " " + str(self.poll)

    @staticmethod
    def was_ticket_used(poll, ticket, signed_ticket):
        return UsedTicket.objects.filter(poll=poll,
                                         ticket=ticket,
                                         signed_ticket=signed_ticket).exists()
