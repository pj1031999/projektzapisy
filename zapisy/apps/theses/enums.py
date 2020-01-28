"""Defines several thesis-related enums.
Using a separate file for these definitions helps prevent
circular dependencies
"""
from enum import Enum
from choicesenum import ChoicesEnum


class ThesisKind(ChoicesEnum):
    MASTERS = 0, "mgr"
    ENGINEERS = 1, "inż"
    BACHELORS = 2, "lic"
    ISIM = 3, "isim"
    # Certain theses will be appropriate for both bachelor and engineer degrees
    BACHELORS_ENGINEERS = 4, "lic+inż"
    BACHELORS_ENGINEERS_ISIM = 5, "lic+inż+isim"


class ThesisStatus(ChoicesEnum):
    BEING_EVALUATED = 1, "weryfikowana przez komisję"
    RETURNED_FOR_CORRECTIONS = 2, "zwrócona do poprawek"
    ACCEPTED = 3, "zaakceptowana"
    IN_PROGRESS = 4, "w realizacji"
    DEFENDED = 5, "obroniona"


class ThesisTypeFilter(Enum):
    """Various values for the "thesis type" filter in the main UI view
    Must match values in backend_callers.ts (this is what client code
    will send to us)
    """
    EVERYTHING = 0
    CURRENT = 1
    ARCHIVED = 2
    MASTERS = 3
    ENGINEERS = 4
    BACHELORS = 5
    BACHELORS_OR_ENGINEERS = 6
    ISIM = 7
    AVAILABLE_MASTERS = 8
    AVAILABLE_ENGINEERS = 9
    AVAILABLE_BACHELORS = 10
    AVAILABLE_BACHELORS_OR_ENGINEERS = 11
    AVAILABLE_ISIM = 12
    UNGRADED = 13

    DEFAULT = EVERYTHING


class ThesisVote(ChoicesEnum):
    NONE = 1, "brak głosu"
    REJECTED = 2, "odrzucona"
    ACCEPTED = 3, "zaakceptowana"
