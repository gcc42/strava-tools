#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import re
from datetime import date, timedelta, datetime

from bs4 import BeautifulSoup

from stravatools._intern.units import Duration, Elevation, Distance

logger = logging.getLogger(__name__)

# Strava data keys.
_ENTITY = 'entity'
_ACTIVITY = 'activity'
_ACTIVITIES = 'activities'
_ACTIVITY_NAME = 'activityName'
_ATHLETE = 'athlete'
_ATHLETE_ID = 'athleteId'
_ATHLETE_NAME = 'athleteName'
_CURSOR_DATA = 'cursorData'
_FEED_TYPE = 'feedType'
_HAS_MORE = 'hasMore'
_ID = 'id'
_ENTRIES = 'entries'
_PAGINATION = 'pagination'
_PREFETCHED_ENTRIES = 'preFetchedEntries'
_ROW_DATA = 'rowData'
_TIME_AND_LOCATION = 'timeAndLocation'
_TYPE = 'type'
_UPDATED_AT = 'updated_at'


def has_more(feed_data):
    return feed_data.get(_PAGINATION, {}).get(_HAS_MORE, False)


def get_cursor(feed_data):
    try:
        return feed_data[_ENTRIES][-1][_CURSOR_DATA][_UPDATED_AT]
    except:
        return None


def club_feed_activites(feed_data):
    # assert feed_data.get(_FEED_TYPE) == 'club'
    return parse_entries(feed_data.get(_ENTRIES, []))


def athlete_feed_activities(feed_data):
    assert feed_data.get(_FEED_TYPE) == 'profile'
    return parse_entries(feed_data.get(_PREFETCHED_ENTRIES, []))


def parse_entries(entries):
    return [a for e in entries if e.get('entity') in ('Activity', 'GroupActivity') for a in parse_entry(e)]


def parse_entry(entry):
    """Parse activity entry from fetched feed."""
    if entry.get('entity') == 'Activity':
        return parse_activity(entry)
    elif entry.get('entity') == 'GroupActivity':
        return parse_group_activity(entry)
    else:
        raise RuntimeError('Error parsing entry', entry)


def parse_activity(entry):
    assert entry.get(_ENTITY, '') == 'Activity'
    activity = entry[_ACTIVITY]
    e = {
        'athlete_id': activity[_ATHLETE][_ATHLETE_ID],
        'athlete_name': decode_unicode_escape(activity[_ATHLETE][_ATHLETE_NAME].replace('\n', ' ')),
        'kind': activity[_TYPE],
        'datetime': parse_timestamp(activity[_TIME_AND_LOCATION]),
        'title': decode_unicode_escape(activity[_ACTIVITY_NAME]),
        'id': activity[_ID],
        'distance': get_stat(activity, 'Distance'),
        'duration': get_stat(activity, 'Time'),
        'elevation': get_stat(activity, 'Elev Gain'),
    }
    return [e, ]


def parse_group_activity(entry):
    timestamp = parse_timestamp(entry[_TIME_AND_LOCATION])
    activities = []
    assert entry[_ROW_DATA]['entity'] == 'GroupActivity'
    for activity in entry[_ROW_DATA][_ACTIVITIES]:
        if activity[_ENTITY] != 'Activity':
            continue
        activities.append({
            'athlete_id': activity['athlete_id'],
            'athlete_name': decode_unicode_escape(activity['athlete_name'].replace('\n', ' ')),
            'kind': activity[_TYPE],
            'datetime': timestamp,
            'title': decode_unicode_escape(activity['name']),
            'id': str(activity['entity_id']),
            'distance': get_stat(activity, 'Distance'),
            'duration': get_stat(activity, 'Time'),
            'elevation': get_stat(activity, 'Elev Gain'),
        })
    return activities


def parse_timestamp(time_and_location) -> datetime:
    """Parse timestamp like Today at 12:48 PM."""
    assert time_and_location.get("timestampFormat", None) == "date_at_time"
    date, time = time_and_location['displayDateAtTime'].lower().split("at")
    return datetime.combine(parse_display_date(date.strip()), datetime.strptime(time.strip(), '%I:%M %p').time())


def parse_display_date(display_date) -> datetime.date:
    """Parse display date like 'today', 'November 1, 2022' etc."""
    display_date = display_date.strip().lower()
    if display_date == 'today':
        return date.today()
    elif display_date == 'yesterday':
        return date.today() - timedelta(days=1)
    else:
        return datetime.strptime(display_date, "%B %d, %Y").date()


def get_stat(activity, stat_name):
    try:
        return _get_stat(activity, stat_name)
    except Exception as e:
        logging.exception('Error fetching stat %s', stat_name)
        return None


def _get_stat(activity, stat_name: str):
    """If stat_one_subtitle has the key 'Distance', then stat_one key stores the distance."""
    stat_name = stat_name.lower()
    if stat_name == 'distance':
        parser = to_distance
    elif stat_name == 'time':
        parser = to_duration
    elif stat_name == 'elev gain':
        parser = to_elevation
    else:
        raise ValueError('Invalid stat_name %s' % stat_name)
    # Find key of the required stat, eg. 'stat_one'.
    try:
        key = [stat['key'] for stat in activity['stats'] if stat['value'].lower() == stat_name][0].split('_subtitle')[0]
    except:
        return None
    value = [stat['value'] for stat in activity['stats'] if stat['key'] == key][0]
    # Unescape unicode escaped HTML and extract text. Parse and return.
    text = BeautifulSoup(decode_unicode_escape(value), "html.parser").text
    return parser(text)


def to_duration(value) -> Duration:
    units = {
        'h': lambda s: int(s) * 60 * 60,
        'm': lambda s: int(s) * 60,
        's': lambda s: int(s),
    }
    m = re.match(r'(\d+)([hms])\s*((\d+)([hms]))?', value.strip())
    if not m:
        raise ValueError('Invalid duration value %s' % value)
    (s1, t1, _, s2, t2) = m.groups()
    duration_sec = units[t1](s1) + (units[t2](s2) if s2 and t2 else 0)
    return Duration(duration_sec)


def to_elevation(value) -> Elevation:
    m = re.match(r'(.+)\s*(km|m)', value.strip())
    if not m:
        raise ValueError('Invalid elevation value %s' % value)
    # remove thousand separator
    num = float(re.sub(r'[^\d\.]', '', m.group(1)))
    if m.group(2) == 'km':
        num = num * 1000
    return Elevation(num)


def to_distance(value) -> Distance:
    m = re.match(r'(.+)\s*(km|m)', value.strip())
    if not m:
        raise ValueError('Invalid distance value %s' % value)
    # remove thousand separator.
    num = float(re.sub(r'[^\d.]', '', m.group(1)))
    if m.group(2) == 'km':
        num = num * 1000
    return Distance(num)


def decode_unicode_escape(text: str):
    """Decode unicode escaped strings like Miko\u0142aj."""
    return bytes(text, 'utf-8').decode('unicode_escape')


if __name__ == '__main__':
    import json

    with open('piobut.txt', 'r', encoding='utf-8') as f:
        data = json.load(f)
    entry0 = data['preFetchedEntries'][0]
    # activity = entry0[_ACTIVITY]
    print(athlete_feed_activities(data))
