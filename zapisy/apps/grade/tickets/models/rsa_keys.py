import json
from django.db import models
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5
from apps.grade.poll.models import Poll
from apps.grade.tickets.models.used_ticket import UsedTicket


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

    def serialize_for_signing_protocol(self):
        """Extracts public parts of the key,
        needed for ticket signing protocol"""
        key = RSA.importKey(self.private_key)
        return {
            'n': str(key.n),
            'e': str(key.e),
        }

    @staticmethod
    def parse_raw_tickets(raw_tickets):
        """Parses raw json containing tickets.
        Raises:
            JSONDecodeError: when provided string is not in json format.
            ValueError: when there is something wrong with internal ticket format,
                for example, some of the requred fields are not provided, type
                of field is incorrect, there are duplicate ids, or id does not
                exist in database.
        Returns:
            Tuple of (valid_polls, error_polls), where error_polls are list of those
            polls, for which signature was incorrect, and valid_polls is list of named tuples,
            containing two fields, ticket_id and poll, where ticket_id can be used to
            track which ticket has already been used to vote.
        """
        tickets = json.loads(raw_tickets)
        tickets_list = tickets['tickets']

        tickets_ids = [ticket['id'] for ticket in tickets_list]

        # Make sure there are no duplicate ids
        if len(tickets_ids) != len(set(tickets_ids)):
            raise ValueError("Duplicate ids detected")

        polls = Poll.objects.filter(pk__in=tickets_ids).select_related('rsakeys').order_by('pk')
        # Make sure all provided ids exist in database
        if len(polls) != len(tickets_list):
            raise ValueError("Provided id doesn't exist in database")
        tickets_list.sort(key=lambda ticket: ticket['id'])

        valid_polls = []
        error_polls = []
        used_polls = []

        for poll, tickets in zip(polls, tickets_list):
            keys = RSAKeys.objects.get(poll=poll)
            ticket = int(tickets['ticket'].encode())
            signed_ticket = int(tickets['signature'].encode())
            if UsedTicket.was_ticket_used(poll, ticket, signed_ticket):
                used_polls.append(poll)
            elif keys.verify_ticket(signed_ticket, ticket):
                valid_polls.append((tickets['ticket'], poll))
                used_ticket = UsedTicket(poll=poll, ticket=ticket, signed_ticket=signed_ticket)
                used_ticket.save()
            else:
                error_polls.append(poll)
        return valid_polls, error_polls, used_polls

    def sign_ticket(self, ticket):
        key = RSA.importKey(self.private_key)
        ticket_hash = SHA256.new(ticket)
        signed_ticket = PKCS1_v1_5.new(key).sign(ticket_hash)
        sign_as_int = int.from_bytes(signed_ticket, 'big')
        return sign_as_int

    def verify_ticket(self, signed_ticket, ticket):
        key = RSA.importKey(self.public_key)
        signature = PKCS1_v1_5.new(key)
        ticket_hash = SHA256.new(bytes(ticket))
        if signature.verify(ticket_hash, signed_ticket):
            return True
        return False
