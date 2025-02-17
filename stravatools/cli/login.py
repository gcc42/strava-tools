import argparse, sys, os
from stravatools.client import Client, Config
import logging


def _args_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('username', type=str, help='Strava username used to login.')
    parser.add_argument('password', type=str, help='Strava password.')
    parser.add_argument('-s', '--save', action='store_true', help='Save credentials to config.')
    return parser


def main(parser: argparse.ArgumentParser) -> None:
    args = parser.parse_args()
    client = Client()
    print('Logging in user %s' % args.username)
    if client.login(args.username, args.password, True, args.save):
        client.close()
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    logging.basicConfig(
        filename=os.path.join(Config.CONFIG_DIR, 'run.log'),
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S')
    main(_args_parser())
