from django.contrib.auth.models import User
from apps.users.models import BaseUser, Employee, is_user_in_group

THESIS_BOARD_GROUP_NAME = "Komisja prac dyplomowych"


def is_theses_board_member(user: User) -> bool:
    """Is the specified user a member of the theses board?"""
    return is_user_in_group(user, THESIS_BOARD_GROUP_NAME)


def get_theses_board():
    """Return all members of the theses board"""
    return Employee.objects.select_related(
        'user'
    ).filter(user__groups__name=THESIS_BOARD_GROUP_NAME)


def get_num_board_members() -> int:
    """Return the number of theses board members"""
    return len(get_theses_board())
