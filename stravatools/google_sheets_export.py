import logging
import os.path

from google import auth
from google.auth.exceptions import DefaultCredentialsError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from stravatools.strava_types import Activity

# Allow read and write of spreadsheets
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# The data range for strava activities. Covers all cells except for the header row.
HEADERS = ['Id', 'Athlete Id', 'Athlete Name', 'Datetime', 'Title', 'Sport', 'Duration', 'Distance', 'Elevation']
# Cell range based on the header row.
DATA_RANGE = 'strava_data!A2:%s' % chr(ord('A') + len(HEADERS) - 1)

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
    # assert result.get('range', '') == DATA_RANGE

    updated_values = update_values(result.get('values', []), activities)
    result = sheet.values().update(spreadsheetId=spreadsheet_id,
                                   range=DATA_RANGE,
                                   valueInputOption='RAW',
                                   body={'values': updated_values}).execute()
    logger.info('Updated %d cells, with %d rows and %d columns'
                % (result.get('updatedCells'), result.get('updatedRows'), result.get('updatedColumns')))
    logger.debug('Updated data: %s' % str(result.get('updatedData')))
    return result.get('updatedCells')


def update_values(values, activities: [Activity]):
    # Dictionary of activity id to value row.
    values_dict = {
        row[0]: row for row in values
    }
    activities_dict = {
        activity.id: convert_to_row(activity) for activity in activities
    }
    values_dict.update(activities_dict)
    # Return rows sorted by datetime.
    datetime_idx = HEADERS.index('Datetime')
    return sorted(values_dict.values(), key=lambda r: r[datetime_idx])


def convert_to_row(activity: Activity) -> [str]:
    """Convert activity object to data row to export."""
    duration_secs = activity.sport.duration.seconds() if activity.sport.duration else ''
    distance_m = activity.sport.distance.m() if activity.sport.distance else ''
    elevation_m = activity.sport.elevation.m() if activity.sport.elevation else ''
    row = [
        activity.id,
        activity.athlete.id,
        activity.athlete.name,
        str(activity.datetime),  # datetime
        activity.title,
        activity.sport.name,
        duration_secs,
        distance_m,
        elevation_m
    ]
    # Convert all the None values to empty strings.
    return [item if item is not None else '' for item in row]
