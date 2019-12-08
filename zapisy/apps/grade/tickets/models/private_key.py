from django.db import models


class PrivateKey(models.Model):
    poll = models.ForeignKey('poll.Poll',
                             verbose_name='ankieta', on_delete=models.CASCADE)
    private_key = models.TextField(verbose_name='klucz prywatny')

    class Meta:
        verbose_name = 'klucz prywatny'
        verbose_name_plural = 'klucze prywatne'
        app_label = 'tickets'

    def __str__(self):
        return f'Klucz prywatny: {self.poll}'

    @staticmethod
    def _int_from_bytes(xbytes: bytes) -> int:
        return int.from_bytes(xbytes, 'big')
