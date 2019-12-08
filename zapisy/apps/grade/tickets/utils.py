from Crypto.PublicKey import RSA
from apps.grade.poll.models import Poll
from apps.grade.tickets.models import PublicKey, PrivateKey
from apps.enrollment.courses.models.semester import Semester


def generate_keys_for_polls():
    poll_list = get_polls()
    generate_keys(poll_list)


# funkcja do ściagania wszystkich ankiet z danego semestru
def get_polls():
    # ew. możliwość wyboru semestru
    semester = Semester.get_current_semester()
    return Poll.get_polls_for_semester(semester)


def generate_keys(poll_list):
    polls_with_keys = []
    for poll in poll_list:
        keys = generate_key()
        polls_with_keys.append((poll, keys))
    save_keys(polls_with_keys)


def save_keys(polls_with_keys):
    # ewentualnie rozdzielić na dwie osobne funkcje dla private and public
    for poll, keys in polls_with_keys: 
        private_key = PrivateKey(poll=poll, private_key=keys[0])
        public_key = PublicKey(poll=poll, public_key=keys[1])
        private_key.save()
        public_key.save()


def generate_key():
    # jakaś zmiana, by nie podawać tego tak jawnie
    length = 1024
    key = RSA.generate(length) 
    private_key = key.exportKey('PEM').decode(encoding='ascii', errors='strict')
    public_key = key.publickey().exportKey('PEM').decode(encoding='ascii', errors='strict')
    return (private_key, public_key)


