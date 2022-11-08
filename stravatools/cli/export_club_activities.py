import argparse, sys
from stravatools.client import Client, Config
import logging


def _args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Export Strava club activities to a spreadsheet')
    parser.add_argument('--spredsheet', type=str, help='Spreadsheet to export to.', required=True)
    parser.add_argument('club_id', type=str, help='ID of the club to export data.', required=True)
    return parser


def main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    client = Client()
    activities_or_error = client.fetch_club_activities(args.club_id)
    if isinstance(activities_or_error, Exception):
        print('Error:', str(activities_or_error))
        sys.exit(1)
    # If activities were fetched successfully, export to spreadsheet.
    spreadsheet = args.spreadsheet
    if client.login(username=args.username, password=args.password, remember=True, save_credentials=args.save):
        client.close()
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(
        filename='/'.join(Config.CONFIG_DIR, 'run.log'),
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S')
    main(_args_parser())
