from apps.grade.poll.models import Poll
from apps.users.models import Student


def student_entitled_to_poll(student: Student, poll: Poll):
    return poll.is_student_entitled_to_poll(student)
