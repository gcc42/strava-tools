import sys, pathlib, json
from pprint import pprint
from stravatools.scraper import StravaScraper, NotLogged
from stravatools._intern.tools import *
from stravatools._intern.units import *

__this_module__ = sys.modules[__name__]

class Client(object):

    def __init__(self, config_dirname=None, cert=None, debug=0):
        self.config = Config(config_dirname)
        self.scraper = StravaScraper(self.config.basepath, self.config['owner_id'], cert, debug)
        self.activities = []
        self.selected_activities = []

    def get_owner(self):
        if self.config['owner_id']:
            return Athlete(self.config['owner_id'], self.config['owner_name'])
        return None

    def last_username(self):
        if self.config['username']:
            return self.config['username']
        return None

    def login(self, username, password, remember=True):
        self.scraper.login(username, password, remember)

        (oid, name) = self.scraper.owner
        self.config['owner_id'] = oid
        self.config['owner_name'] = name
        self.config['username'] = username
        self.store_activities()

    def logout(self):
        self.scraper.logout()

    def load_activity_feed(self, next=False, num=20):
        if next: self.scraper.load_feed_next()
        else:    self.scraper.load_dashboard(min(max(1, num), 100))
        return self.store_activities()

    def store_activities(self):
        activities = set(list(map(lambda a: Activity(self, a), self.scraper.activities())))
        activities.update(set(self.activities))
        new = len(activities) - len(self.activities)
        self.activities = sorted(list(activities), reverse=True, key=lambda x: x.datetime)
        return (new, len(self.activities))

    def select_activities(self, predicate):
        self.selected_activities = list(filter(predicate, self.activities))

    def close(self):
        self.config.save()
        self.scraper.save_state()

    def load_page(self, page):
        self.scraper.load_page(page)
        return self.store_activities()


class Config(object):
    CONFIG_DIR = '/'.join((str(pathlib.Path.home()), '.strava-tools'))
    FILE = 'config.json'
    data = {}

    def __init__(self, config_dirname=None):
        self.basepath = pathlib.Path(config_dirname if config_dirname else Config.CONFIG_DIR)
        self.basepath.mkdir(parents=True, exist_ok=True)
        self.data = self.__load(Config.FILE)

    def __getitem__(self, key):
        if key in self.data:
            return self.data.get(key)
        return None

    def __setitem__(self, key, value):
        self.data[key] = value

    def __load(self, filename):
        path = self.basepath / filename
        try:
            with path.open() as file:
                return json.loads(file.read())
        except: return {}

    def __save(self, data, filname):
        with (self.basepath / filname).open('w') as file:
            file.write(json.dumps(data))

    def save(self):
        self.__save(self.data, Config.FILE)


class Model(object):
    def __repr__(self):
        attrs = [
            '{0}={1}'.format(x, self.__getattribute__(x))
            for x in ['id','name']
            if hasattr(self, x)
        ]
        return '<{0} {1}>'.format(self.__class__.__name__, ' '.join(attrs))

class Activity(Model):
    def __init__(self, client, scraped):
        self.client = client
        self.id = scraped.get('id')
        self.athlete = Athlete.of(scraped)
        self.datetime = scraped.get('datetime')
        self.title = scraped.get('title')
        self.sport = Sport.of(scraped)
        self.kudoed = scraped.get('kudoed')
        self.kudos = 0
        self.dirty = False

    def send_kudo(self):
        sent = self.client.scraper.send_kudo(self.id)
        if sent:
            self.kudoed = True
            self.dirty = True
        return sent

    def __eq__(self, other): 
        if not isinstance(other, Activity):
            return False

        return self.id == other.id

    def __hash__(self): 
            return hash(self.id)

class Athlete(Model):
    def __init__(self, id, name):
        self.id = id
        self.name = name

    @classmethod
    def of(cls, data):
        return cls(data.get('athlete_id'), data.get('athlete_name'))

class Sport(Model):
    def __init__(self, scraped):
        self.name = scraped.get('kind')
        self.duration = scraped.get('duration')
        self.distance = scraped.get('distance')
        self.elevation = scraped.get('elevation')

    def velocity(self):
        return UNIT_EMPTY

    def of(scraped):
        kind = scraped.get('kind')
        if hasattr(__this_module__, kind):
            return getattr(__this_module__, kind)(scraped)
        return Sport(scraped)

class Run(Sport):
    def velocity(self):
        return Pace(self.duration, self.distance, 'minkm')

class Bike(Sport):
    def velocity(self):
        return Speed(self.duration, self.distance, 'kmh')

class Swim(Sport):
    def velocity(self):
        return Pace(self.duration, self.distance, 'min100m')

class Kitesurf(Sport):
    def velocity(self):
        return Speed(self.duration, self.distance, 'kn')

class Climbing(Sport):
    pass

class Hike(Run):
    pass

class EBike(Bike):
    pass

class VBike(Bike):
    pass

class Walk(Run):
    pass

class Yoga(Sport):
    pass

class Workout(Sport):
    pass

class Weight(Sport):
    pass

















