SCHEDULER_BASE = 'http://scheduler.gtch.eu'

URL_LOGIN = SCHEDULER_BASE + '/admin/login/'
URL_CONFIG = SCHEDULER_BASE + '/scheduler/api/config/{id}/'

SLACK_WEBHOOK_URL = (
    'https://hooks.slack.com/services/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'
)

# The mapping between group types in scheduler and enrollment system
# w (wykład), p (pracownia), c (ćwiczenia), s (seminarium), r (ćwiczenio-pracownia),
# e (repetytorium), o (projekt)
GROUP_TYPES = {'w': '1', 'e': '9', 'c': '2', 'p': '3',
               'r': '5', 's': '6', 'o': '10'}

# The default limits for group types
LIMITS = {'1': 300, '9': 300, '2': 20, '3': 15, '5': 18, '6': 15, '10': 15}

COURSES_MAP = {
    'PRAKTYKA ZAWODOWA - 3 TYGODNIE': 'PRAKTYKA ZAWODOWA - TRZY TYGODNIE',
    'PRAKTYKA ZAWODOWA - 4 TYGODNIE': 'PRAKTYKA ZAWODOWA - CZTERY TYGODNIE',
    'PRAKTYKA ZAWODOWA - 5 TYGODNI': 'PRAKTYKA ZAWODOWA - PIĘĆ TYGODNI',
    'PRAKTYKA ZAWODOWA - 6 TYGODNI': 'PRAKTYKA ZAWODOWA - SZEŚĆ TYGODNI'
}

COURSES_DONT_IMPORT = [
    'ALGEBRA I',
    'ALGEBRA LINIOWA 2',
    'ALGEBRA LINIOWA 2R',
    'ANALIZA MATEMATYCZNA II',
    'FUNKCJE ANALITYCZNE 1',
    'RÓWNANIA RÓŻNICZKOWE 1',
    'RÓWNANIA RÓŻNICZKOWE 1R',
    'TEORIA PRAWDOPODOBIEŃSTWA 1',
    'TOPOLOGIA']
