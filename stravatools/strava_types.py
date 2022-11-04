import sys

from stravatools._intern.units import UNIT_EMPTY, Pace, Speed

__this_module__ = sys.modules[__name__]


class Model(object):
    def __repr__(self):
        attrs = [
            '{0}={1}'.format(x, self.__getattribute__(x))
            for x in ['id', 'name']
            if hasattr(self, x)
        ]
        return '<{0} {1}>'.format(self.__class__.__name__, ' '.join(attrs))


class Activity(Model):
    def __init__(self, scraped):
        self.id = scraped.get('id')
        self.athlete = Athlete.of(scraped)
        self.datetime = scraped.get('datetime')
        self.title = scraped.get('title')
        self.sport = Sport.of(scraped)
        # self.kudoed = scraped.get('kudoed')
        # self.kudos = 0
        # self.dirty = False

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


class Walk(Run):
    pass


class Hike(Run):
    pass


class Golf(Run):
    pass


class EBike(Bike):
    pass


class VBike(Bike):
    pass


class Yoga(Sport):
    pass


class Climbing(Sport):
    pass


class Workout(Sport):
    pass


class Weight(Sport):
    pass
