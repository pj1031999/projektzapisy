import gspread
from oauth2client.service_account import ServiceAccountCredentials

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


def create_sheets_service(id):
    credentials = ServiceAccountCredentials.from_json_keyfile_name('apps/offer/plan/Credentials.json', SCOPES)
    gc = gspread.authorize(credentials)
    sh = gc.open_by_key(id).sheet1
    return sh
