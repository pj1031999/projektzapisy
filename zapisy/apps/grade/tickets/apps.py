from django.apps import AppConfig


class TicketsAppConfig(AppConfig):
    name = "apps.grade.tickets"
    verbose_name = "Tickets"

    def ready(self):
        import apps.grade.tickets.signals
