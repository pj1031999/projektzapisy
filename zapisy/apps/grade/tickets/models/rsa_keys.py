from django.db import models
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5


class RSAKeys(models.Model):
    poll = models.OneToOneField('poll.Poll',
                                verbose_name='ankieta',
                                on_delete=models.CASCADE)
    private_key = models.TextField(verbose_name='klucz prywatny')
    public_key = models.TextField(verbose_name='klucz publiczny')

    class Meta:
        verbose_name = 'klucze RSA'
        verbose_name_plural = 'klucze RSA'
        app_label = 'tickets'

    def __str__(self):
        return f'Klucze RSA: {self.poll}'

    def sign_ticket(self, ticket):
        key = RSA.importKey(self.private_key)
        ticket_hash = SHA256.new(ticket)
        signature = PKCS1_v1_5.new(key).sign(ticket_hash)
        sign_as_int = int.from_bytes(signature, 'big')
        return sign_as_int
