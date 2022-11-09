import argparse, sys, os
import logging
from stravatools.client import Client, Config
from stravatools.google_sheets_export import export_activities
from stravatools.strava_types import Activity
from datetime import datetime
from stravatools.feed_data_parser import to_distance, to_duration, to_elevation


def _args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Export Strava club activities to a spreadsheet')
    parser.add_argument('--spreadsheet', type=str, help='Spreadsheet to export to.', required=True)
    parser.add_argument('club_id', type=str, help='ID of the club to export data.')
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
    activities_or_error = client.fetch_club_activities(args.club_id)
    if isinstance(activities_or_error, Exception):
        print('Error:', str(activities_or_error))
        sys.exit(1)
    # If activities were fetched successfully, export to spreadsheet.
    spreadsheet = args.spreadsheet
    print('Fetched %d activities from the club.' % len(activities_or_error))
    try:
        updated = export_activities(activities_or_error, spreadsheet)
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
