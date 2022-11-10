import argparse
import logging
import os
from datetime import datetime

from stravatools.client import Client, Config
from stravatools.feed_data_parser import to_distance, to_duration
from stravatools.google_sheets_export import export_activities
from stravatools.strava_types import Activity


def _args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Export Strava user activity feed to a spreadsheet')
    parser.add_argument('--spreadsheet', type=str, help='Id of the Google Sheet to export to', required=True)
    parser.add_argument(
        '-m', '--month',
        type=lambda s: datetime.strptime(s, '%Y-%m'),
        action='append',
        required=False,
        help='A list of months (in the YYYY-mm format) for which to export activities')
    parser.add_argument('athlete_id', type=str, help='Athlete id for which to export data')
    return parser


SAMPLE_ACTIVITY = Activity({
    'id': '8081105545',
    'datetime': datetime.now(),
    'title': 'Sample Activity',
    'athlete_id': '109319531',
    'athlete_name': 'TheChamp',
    'kind': 'Run',
    'distance': to_distance('2 km'),
    'duration': to_duration('30m 20s'),
    'elevation': None
})


def main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    client = Client()
    # Use the default (month=None) feed if the month list is not specified.
    month_list = args.month if args.month is not None else [None]
    # Fetch activities for each month arg specified and collect them in a list.
    all_activities = []
    for month in month_list:
        activities_or_error = client.fetch_athlete_activities(args.athlete_id, month=month)
        if isinstance(activities_or_error, Exception):
            print('Error fetching activities for month %s:' % month, str(activities_or_error))
        else:
            all_activities.extend(activities_or_error)
    # If activities were fetched successfully, export to spreadsheet.
    spreadsheet = args.spreadsheet
    print('Fetched %d activities for athlete %s.' % (len(all_activities), args.athlete_id))
    try:
        updated = export_activities(all_activities, spreadsheet)
        print('Updated %d cells' % updated)
    except Exception as e:
        print('Error while exporting activities:', e)


if __name__ == '__main__':
    logging.basicConfig(
        filename=os.path.join(Config.CONFIG_DIR, 'run.log'),
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S')
    main(_args_parser())
