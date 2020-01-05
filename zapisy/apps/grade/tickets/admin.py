from django.contrib import admin
from apps.grade.tickets.models.rsa_keys import RSAKeys
from apps.grade.tickets.models.used_ticket import UsedTicket

admin.site.register(RSAKeys)
admin.site.register(UsedTicket)
