import argparse, sys
from stravatools.client import Client, Config
import logging


def _args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('username', type=str, help='Strava username used to login.')
    parser.add_argument('password', type=str, help='Strava password.')
    parser.add_argument('-s', '--save', action='store_true', help='Save credentials to config.')
    return parser


def main(parser) -> None:
    args = parser.parse_args()
    client = Client()
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
