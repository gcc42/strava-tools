import pathlib, json, logging, os

from stravatools.scraper import StravaScraper
from stravatools.strava_types import Activity, Athlete

logger = logging.getLogger(__name__)


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

    def login(self, username, password, remember=True, save_credentials=False):
        try:
            self.scraper.login(username, password, remember)
            (oid, name) = self.scraper.owner
            self.config['owner_id'] = oid
            self.config['owner_name'] = name
            self.config['username'] = username
            if save_credentials:
                self.config['password'] = password
            return True
        except Exception as e:
            logger.exception('Error while logging in')
            return False
        # self.store_activities()

    def logout(self):
        self.scraper.logout()

    def verify_login(self):
        if self.scraper.is_logged_in():
            return
        if self.config['username'] and self.config['password']:
            self.login(self.config['username'], self.config['password'], remember=True)
        else:
            raise RuntimeError('Not logged in and no credentials available')

    def load_activity_feed(self, athlete_id=0, next=False, num=20):
        if next:
            self.scraper.load_feed_next(athlete_id)
        else:
            self.scraper.load_dashboard(athlete_id, min(max(1, num), 100))
        return self.store_activities()

    def fetch_club_activities(self, club_id):
        """
        Fetch all the activities from club_id (strava only shows the last 100 activities).

        Returns a list of Activities or Exception.
        """
        entries = []
        try:
            self.verify_login()
            cursor, has_more, fetched_entries = self.scraper.fetch_club_activites(club_id)
            entries.append(fetched_entries)
            logger.info('Fetched %d entries from club feed:\n%s' % (len(fetched_entries), fetched_entries))
            while cursor and has_more:
                cursor, has_more, fetched_entries = self.scraper.fetch_club_activites(club_id, cursor=cursor)
                entries.append(fetched_entries)
                logger.info('Fetched %d entries from club feed:\n%s' % (len(fetched_entries), fetched_entries))
            return [Activity(a) for a in entries]
        except Exception as e:
            logger.exception('Error while fetching club')
            return e

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

    def send_kudos(self, activity: Activity):
        return self.scraper.send_kudo(activity.id)


class Config(object):
    CONFIG_DIR = os.path.join(str(pathlib.Path.home()), '.strava-tools')
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
        except:
            return {}

    def __save(self, data, filename):
        with (self.basepath / filename).open('w') as file:
            file.write(json.dumps(data))

    def save(self):
        self.__save(self.data, Config.FILE)
