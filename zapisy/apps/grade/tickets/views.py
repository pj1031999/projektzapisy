import json
from django.db import transaction
from django.http import HttpResponseBadRequest, HttpResponse
from apps.users.decorators import student_required
from apps.grade.poll.models.poll import Poll
from apps.grade.tickets.models.rsa_keys import RSAKeys
from apps.grade.tickets.models.generated_ticket import GeneratedTicket
from apps.grade.tickets.models.used_ticket import UsedTicket


@student_required
@transaction.atomic
def sign_the_ticket(request):
    """Signs the ticket send by student and returns poll id,
    ticket and signed ticket contained in JSON.
    Creates GeneratedTicket object after signing the ticket.
    Receives ticket and poll_id from POST request (keys: 'ticket' and 'poll')
    """
    ticket_dict = {}
    ticket_dict["ticket"] = request.POST.get("ticket", "")
    ticket_dict["poll_id"] = request.POST.get("poll", "")
    poll = Poll.objects.get(id=ticket_dict["poll_id"])
    err_msg = None

    if not poll.is_student_entitled_to_poll(request.user.student):
        err_msg = "Student nie jest upoważniony do tej ankiety"
    elif GeneratedTicket.student_generated_ticket(poll, request.user.student):
        err_msg = "Student już stworzył bilet dla tej ankiety"

    if err_msg:
        return HttpResponseBadRequest(err_msg)

    keys = RSAKeys.objects.filter(poll=poll).select_for_update().get()
    ticket_dict["signed_ticket"] = keys.sign_ticket(ticket_dict["ticket"])

    generated_ticket = GeneratedTicket(keys=keys,
                                       student=request.user.student)
    generated_ticket.save()

    response = json.dumps(ticket_dict)

    return HttpResponse(response)


def verify_signed_ticket(request):
    """Verifies signed ticket send by anonymous student
    and returns HTTP 200 response code.
    Creates UsedTicket object after verifying signature.
    Receives ticket and poll_id from POST request (keys: 'ticket' and 'poll')
    """
    ticket = request.POST.get("ticket", "")
    signed_ticket = request.POST.get("signed_ticket", "")
    poll_id = request.POST.get("poll", "")
    poll = Poll.objects.get(id=poll_id)

    err_msg = None
    if UsedTicket.was_ticket_used(poll, ticket, signed_ticket):
        err_msg = "Bilet już wykorzystany w głosowaniu"
    if err_msg:
        return HttpResponseBadRequest(err_msg)

    key = RSAKeys.objects.get(poll=poll)
    if not key.verify_ticket(signed_ticket, ticket):
        err_msg = "Błąd weryfikacji klucza"
    if err_msg:
        return HttpResponseBadRequest(err_msg)

    used_ticket = UsedTicket(poll=poll, ticket=ticket,
                             signed_ticket=signed_ticket)
    used_ticket.save()

    return HttpResponse("OK")
