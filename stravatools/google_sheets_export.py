import logging, os.path

from google import auth
from google.auth.transport.requests import Request
from google.auth.exceptions import DefaultCredentialsError
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from stravatools.strava_types import Activity

# Allow read and write of spreadsheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The data range for strava activities. Covers all cells except for the header row.
DATA_RANGE = 'strava_data!A2:H'
HEADERS = ['Id', 'Athlete Id', 'Datetime', 'Title', 'Sport', 'Duration', 'Distance', 'Elevation']

logger = logging.getLogger(__name__)


def get_file_creds():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def get_application_default_creds():
    """Return application default credentials for the current environment."""
    creds, project_id = auth.default(scopes=SCOPES)
    return creds


def get_creds():
    try:
        return get_application_default_creds()
    except DefaultCredentialsError as e:
        logger.error('Could not fetch application default credentials, '
                     'trying to retrieve from credentials.json')
        try:
            return get_file_creds()
        except Exception as e:
            logger.exception('Error fetching file credentials')
            return None


def export_activities(activities: [Activity], spreadsheet_id: str):
    """Export activities to a spreadsheet with the given id, sheet name 'strava_data'."""
    creds = get_creds()
    if not creds:
        raise RuntimeError('Could not retrieve credentials.')
    service = build('sheets', 'v4', credentials=creds)

    # Call the Sheets API
    sheet = service.spreadsheets()
    result = sheet.values().get(spreadsheetId=spreadsheet_id,
                                range=DATA_RANGE).execute()
    assert result.get('range', '') == DATA_RANGE

    updated_values = update_values(result.get('values', []), activities)
    result = sheet.values().update(spreadsheetId=spreadsheet_id,
                                   range=DATA_RANGE,
                                   valueInputOption='RAW',
                                   body={'values': updated_values}).execute()
    logger.info('Updated %d cells, with %d rows and %d columns'
                % (result.get('updatedCells'), result.get('updatedRows'), result.get('updatedColumns')))
    logger.debug('Updated data: %s' % str(result.get('updatedData')))


def update_values(values, activities: [Activity]):
    # Dictionary of activity id to value row
    values_dict = {
        row[0]: row for row in values
    }
    activities_dict = {
        activity.id: convert_to_row(activity) for activity in activities
    }


def convert_to_row(activity: Activity) -> [str]:
    """Convert activity object to data row to export."""

    [
        activity.id,
        activity.athlete.id,

    ]
