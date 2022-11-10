import logging
import os

from stravatools import __version__
from stravatools.client import Client, Config
from stravatools.shell import commands
# If Pull Request accepted: from click_shell import shell
from stravatools.shell.click_shell_plus import shell
from stravatools.shell.commands import *

histfile = os.path.join(os.path.expanduser("~"), ".strava_history")


def close_client(ctx):
    ctx.obj['client'].close()


@shell(prompt='strava >> ', intro='Strava Shell %s' % __version__, hist_file=histfile, on_finished=close_client)
@click.option('--cert', help='Path SSL certificat Root CA')
@click.option('-v', '--verbose', count=True)
@click.pass_context
def cli_shell(ctx, cert, verbose):
    client = ctx.obj['client']
    greeting(client)


for command in commands.__dict__.values():
    if isinstance(command, click.core.Command):
        cli_shell.add_command(command)


@click.command()
@click.option('--cert', help='Path SSL certificat Root CA')
@click.option('-v', '--verbose', count=True)
def main(cert, verbose):
    cli_shell(obj={'client': Client(cert=cert, debug=verbose)})


if __name__ == '__main__':
    logging.basicConfig(
        filename=os.path.join(Config.CONFIG_DIR, 'shell_run.log'),
        level=logging.INFO,
        format='%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d:%H:%M:%S')
    main()
