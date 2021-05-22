import click, getpass, sys, time
from click_spinner import spinner

import cmd, texttables, datetime
from functools import partial
from stravatools.scraper import NotLogged, WrongAuth
from stravatools import __version__
from stravatools._intern.tools import *


@click.command()
@click.argument('file', type=click.Path(exists=True))
@click.pass_context
def sample(ctx, file):
    (new, total) = ctx.obj['client'].load_page(file)
    print('Loaded %d activities' % new)

@click.command()
@click.pass_context
def login(ctx):
    '''Login to Strava (www.strava.com)
  You will be asked to provider you username (email) and password
  and eventually store a cookie to keep your strava session open'''
    
    try:
        client = ctx.obj['client']
        username = click.prompt('Username', default=client.last_username())
        password = click.prompt('Password', hide_input=True)
        remember = click.confirm('Remember session ?', default=True)
        with spinner():
            client.login(username, password, remember)
        greeting(ctx.obj['client'])
    except WrongAuth:
        print('Username or Password incorrect')

@click.command()
@click.pass_context
def logout(ctx):
    '''Simply clean your cookies session if any was store'''

    ctx.obj['client'].logout()
    print('Logged out')

@click.command()
@click.option('--all', is_flag=True, help='Loads all available activities from activity feed')
@click.option('--next', is_flag=True, help='Loads next activity from activity feed. Usually this will load the next 30 activities')
@click.argument('n', default=20)
@click.pass_context
def load(ctx, all, next, n):
    '''Loads [n] activity feed from Strava and store activities default 20)'''

    def load():
        client = ctx.obj['client']
        if all:
            (new, total) = client.load_activity_feed(num=100)
            s = new
            while new > 0:
                (new, total) = client.load_activity_feed(next = True)
                s = s + new
            new = s
        else:
            (new, total) = client.load_activity_feed(next=next, num=n)
        return new

    with spinner():
        new = load()

    print('Loaded %d activities' % new)

@click.command()
@click.option('-a', '--athlete', multiple=True, help='Filter and display activities that pattern match the athlete name')
@click.option('-s', '--sport', multiple=True, help='Filter and display activities that pattern match the athlete sport')
@click.option('-K/-k', '--kudoed/--no-kudoed', is_flag=True, default=None, help='Filter and display activities you haven''t sent a kudo')
@click.pass_context
def activities(ctx, athlete, sport, kudoed):
    '''Dispaly loaded activity and filters are used to select activities
  <pattern> [-]<string> ('-' negate)'''

    class dialect(texttables.Dialect):
        header_delimiter = '-'

    name_includes = list(filter(lambda x: x[0] != '-', athlete))
    name_excludes = list(map(lambda x: x[1:], filter(lambda x: len(x) > 1 and x[0] == '-', athlete)))
    kudoed_predicate = filter_kudo(kudoed) if kudoed != None else lambda x: True

    client = ctx.obj['client']
    client.select_activities(all_predicates((
        kudoed_predicate,
        build_predicate_list(partial(filter_name, contains), name_includes),
        build_predicate_list(partial(filter_name, not_contains), name_excludes),
        build_predicate_list(partial(filter_sport, contains), sport))))

    print('Activities %d/%d' % (len(client.selected_activities), len(client.activities)))
    if len(client.selected_activities) > 0:
        mapper = {
            'Kudo': lambda a: '*' if a.dirty else u'\u2713' if a.kudoed else '',
            'Time': lambda a: datetime.datetime.strftime(a.datetime, '%Y-%m-%d %H:%M:%S %Z'),
            'Athlete': lambda a: a.athlete.name,
            'Sport': lambda a: a.sport.name,
            'Duration': lambda a: a.sport.duration.for_human(),
            'Distance': lambda a: a.sport.distance.for_human(),
            'Elevation': lambda a: a.sport.elevation.for_human(),
            'Velocity': lambda a: a.sport.velocity().for_human(),
            'Title': lambda a: a.title,
        }
        make_entry = lambda activity: [ (header, mapper(activity)) for header,mapper in mapper.items() ]
        data = list(map(dict, map(make_entry, client.selected_activities[::-1])))
        with texttables.dynamic.DictWriter(sys.stdout, list(mapper.keys()), dialect=dialect) as w:
            w.writeheader()
            w.writerows(data)


@click.command()
@click.pass_context
def kudo(ctx):
    '''Send kudo to all filtered activities'''

    for activity in filter(filter_kudo(False), ctx.obj['client'].selected_activities):
        print('Kudoing %s for %s .. ' % (activity.athlete.name, activity.title), end='')
        if activity.send_kudo(): print('Ok')
        else: print('Failed')
        # Sleep to limit the rate not to be banned from the provider
        time.sleep(1.1)


def greeting(client):
    if client.get_owner():
        click.secho('Welcome %s' % client.get_owner().name)

def filter_name(predicate, param):
    return lambda activity: predicate(param, activity.athlete.name)
def filter_sport(predicate, param):
    return lambda activity: predicate(param, activity.sport.name)
def filter_kudo(sent):
    return lambda activity: eq_bool(sent, activity.kudoed)
