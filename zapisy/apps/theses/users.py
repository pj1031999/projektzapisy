from django.contrib.auth.models import User
from apps.users.models import BaseUser, Employee, is_user_in_group

THESIS_BOARD_GROUP_NAME = "Komisja prac dyplomowych"


def is_theses_board_member(user: User) -> bool:
    """Is the specified user a member of the theses board?"""
    return is_user_in_group(user, THESIS_BOARD_GROUP_NAME)
