#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests, http, time, traceback, sys, re, os

from bs4 import BeautifulSoup
from datetime import datetime
from pprint import pprint

from stravatools import __version__
from stravatools._intern.tools import *
from stravatools._intern.units import *

class StravaScraper(object):
    USER_AGENT = "stravatools/%s" % __version__
    BASE_HEADERS = {'User-Agent': USER_AGENT}
    CSRF_H = 'x-csrf-token'
    
    SESSION_COOKIE='_strava4_session'

    BASE_URL = "https://www.strava.com"
    URL_LOGIN = "%s/login" % BASE_URL
    URL_SESSION = "%s/session" % BASE_URL
    URL_DASHBOARD = "%s/dashboard/following/%%d" % BASE_URL
    URL_DASHBOARD_FEED = "%s/dashboard/feed?feed_type=following&athlete_id=%%s&before=%%s&cursor=%%s" % BASE_URL
    URL_SEND_KUDO = "%s/feed/activity/%%s/kudo" % BASE_URL

    soup = None
    response = None
    csrf_token = None
    feed_cursor = None
    feed_before = None

    def __init__(self, cookie_dir, owner_id=None, cert=None, debug=0):
        self.cookies_path = cookie_dir / 'cookies.txt'
        self.owner = (owner_id, None)
        self.cert = cert
        self.debug = debug
        self.session = self.__create_session(owner_id == None)
        self.get = lambda url, logged=True, allow_redirects=True: self.__store_response(self.__get(url, logged, allow_redirects))
        self.post = lambda url, data=None, logged=True, allow_redirects=True: self.__store_response(self.__post(url, data, logged, allow_redirects))

    def __create_session(self, fresh):
        session = requests.Session()
        cookies = http.cookiejar.MozillaCookieJar(str(self.cookies_path))
        if not fresh:
            try: cookies.load()
            except OSError: pass
        session.cookies = cookies
        return session

    def __get(self, url, logged=True, allow_redirects=True):
        headers = StravaScraper.BASE_HEADERS
        self.__debug_request(url, headers)
        response = self.session.get(url, headers=headers, verify=self.cert, allow_redirects=allow_redirects)
        self.__debug_response(response)
        self.__check_response(response, logged)
        return response

    def __post(self, url, data=None, logged=True, allow_redirects=True):
        csrf_header = {}
        if self.csrf_token: csrf_header[StravaScraper.CSRF_H] = self.csrf_token

        headers = {**StravaScraper.BASE_HEADERS, **csrf_header}
        self.__debug_request(url, headers)
        if data:
            response = self.session.post(url, data=data, headers=headers, verify=self.cert, allow_redirects=allow_redirects)
        else:
            response = self.session.post(url, headers=headers, verify=self.cert, allow_redirects=allow_redirects)
        self.__debug_response(response)
        self.__check_response(response, logged)
        return response

    def __check_response(self, response, logged=False):
        response.raise_for_status()
        if logged and "class='logged-out" in response.text:
            raise NotLogged()
        return response

    def __debug_request(self, url, headers):
        if self.debug > 0:
            print('>>> GET %s' % url)
            print('>>> Headers')
            pprint(headers)

    def __debug_response(self, response):
        if self.debug > 0:
            print('<<< Status %d' % response.status_code)
            print('<<< Headers')
            pprint(response.headers)
            if self.debug > 1 and 'Content-Type' in response.headers:
                print('<<< Body')
                if response.headers['Content-Type'] == 'text/html':
                    print(response.text)
                elif response.headers['Content-Type'] == 'application/json':
                    pprint(json.loads(response.text))
                else:
                    print(response.text)


    def __store_response(self, response):
        self.response = response
        self.soup = BeautifulSoup(response.text, 'lxml')
        meta = first(self.soup.select('meta[name="csrf-token"]'))
        if meta:
            self.csrf_token = meta.get('content')
        return response

    def __print_traceback(self):
        if self.debug > 0: traceback.print_exc(file=sys.stdout)

    def save_state(self):
        self.session.cookies.save()
        
    def login(self, email, password, remember_me=True):
        # If the client was logged, we safely logout first
        self.logout()
        self.get(StravaScraper.URL_LOGIN, logged=False)
        soup = BeautifulSoup(self.response.content, 'lxml')
        utf8 = soup.find_all('input',
                             {'name': 'utf8'})[0].get('value').encode('utf-8')
        token = soup.find_all('input',
                              {'name': 'authenticity_token'})[0].get('value')
        login_data = {
            'utf8': utf8,
            'authenticity_token': token,
            'plan': "",
            'email': email,
            'password': password
        }
        if remember_me:
            login_data['remember_me'] = 'on'

        self.post(StravaScraper.URL_SESSION, login_data, logged=False, allow_redirects=False)
        if self.response.status_code == 302 and self.response.headers['Location'] == StravaScraper.URL_LOGIN:
            raise WrongAuth()

        self.load_dashboard()
        try:
            assert("Log Out" in self.response.text)
            profile = first(self.soup.select('div.athlete-profile'))
            self.owner = (
                first(profile.select('a'), tag_get('href', lambda x:x.split('/')[-1])),
                first(profile.select('div.athlete-name'), tag_string())
            )
        except Exception as e:
            self.__print_traceback()
            raise UnexpectedScrapped('Profile information cannot be retrieved', self.soup.text)

    def logout(self):
        self.session.cookies.clear()

    def send_kudo(self, activity_id):
        try:
            response = self.post(StravaScraper.URL_SEND_KUDO % activity_id)
            return response.json()['success'] == 'true'
        except Exception as e:
            self.__print_traceback()
            return False

    def load_page(self, path='page.html'):
        with open(path, 'r') as file:
            self.soup = BeautifulSoup(file.read(), 'lxml')

    def load_dashboard(self, num=30):
        self.get(StravaScraper.URL_DASHBOARD % (num+1))
        self.__store_feed_params()

    def load_feed_next(self):
        self.get(StravaScraper.URL_DASHBOARD_FEED % (self.owner[0], self.feed_before, self.feed_cursor))
        self.__store_feed_params()

    def __store_feed_params(self):
        remove_UTC = lambda x:x.replace(' UTC','')

        cards = list(self.soup.select('div.activity.feed-entry.card'))
        ranks = list(each(cards, tag_get('data-rank')))
        updated = list(each(cards, tag_get('data-updated-at')))
        datetimesUTC = list(each(self.soup.select('div.activity.feed-entry.card time time'), tag_get('datetime')))
        datetimes = list(map(remove_UTC, datetimesUTC))
        entries = list(zip(ranks, updated, datetimes))
        if len(entries) > 0:
            self.feed_cursor = sorted(entries, key=lambda data:data[0])[0][0]
            self.feed_before = sorted(entries, key=lambda data:data[2])[0][1]

    def activities(self):
        activities = list(self._activities(self.soup.select('div.activity')))
        for group in self.soup.select('div.group-activity'):
            timeTag = group.select('time')
            sportTag = group.select('.group-activity-icon .app-icon-wrapper .app-icon')
            activities = activities + list(self._activities(group.select('li.activity'), timeTag, sportTag))
        return activities

    def _activities(self, selected_activities, timeTag=None, sportTag=None):
        for activity in selected_activities:
            try:
                ts = timeTag if timeTag else activity.select('time')
                st = sportTag if sportTag else activity.select('.entry-body .media .app-icon')

                entry = {
                    'athlete_name': first(activity.select('a.entry-owner'), tag_string()),
                    'kind': first(st, extract_sport()),
                    'datetime': first(ts, tag_get('datetime', parse_datetime('%Y-%m-%d %H:%M:%S %Z'))),
                    'title': first(activity.select('h3 a'), tag_string()),
                    'id': first(activity.select('h3 a'), tag_get('href', lambda x: x.split('/')[-1])),
                    'distance': find_stat(activity, r'\s*Distance\s*(.+)\s', to_distance),
                    'duration': find_stat(activity, r'\s*Time\s*(.+)\s', to_duration),
                    'elevation':find_stat(activity, r'\s*Elev Gain\s*(.+)\s', to_elevation),
                    'kudoed': first(activity.select('div.entry-footer div.media-actions button.js-add-kudo')) is None
                }

                yield entry
            except Exception as e:
                print(e)
                self.__print_traceback()
                if self.debug > 0:
                    print("Unparsable %s" % activity)

    # Utility functions
def tag_string(mapper=identity):
    return lambda tag: mapper(tag.string.replace('\n',''))
def tag_get(attr, mapper=identity):
    return lambda tag: mapper(tag.get(attr))
def parse_datetime(pattern):
    return lambda value: datetime.strptime(value, pattern)
def has_class(tag, predicate):
    return any_match(tag.get('class'), predicate)
def extract_sport():
    class_sports = {
    'run':'Run',
    'ebikeride':'EBike',
    'virtualride':'VRide',
    'ride':'Bike',
    'ski':'Ski',
    'swim':'Swim',
    'rockclimbing':'Climbing',
    'hike':'Hike',
    'walk':'Walk',
    'yoga':'Yoga',
    'workout':'Workout',
    'weighttraining':'Weight',
    'kitesurf':'Kitesurf',
    'golf':'Golf',
    '':'Sport' # Must defined at last position
    }
    return lambda tag: first([ v 
        for k,v in class_sports.items()
        if has_class(tag, lambda cls: contains(k, cls)) ])

def to_distance(value):
    m = re.search(r'\s*(.+)\s+(km|m)\s*', value)
    if m:
        # remove thousand separator
        num = float(re.sub(r'[^\d\.]', '', m.group(1)))
        if m.group(2) == 'km':
            num = num * 1000
        return Distance(num)
    return UNIT_EMPTY

def to_elevation(value):
    m = re.search(r'\s*(.+)\s+(km|m)\s*', value)
    if m:
        # remove thousand separator
        num = float(re.sub(r'[^\d\.]', '', m.group(1)))
        if m.group(2) == 'km':
            num = num * 1000
        return Elevation(num)
    return UNIT_EMPTY


def to_duration(value):
    units = {
        'h': lambda s: int(s) * 60 * 60,
        'm': lambda s: int(s) * 60,
        's': lambda s: int(s),
    }
    m = re.search(r'\s*(\d+)([hms])\s+(\d+)([hms])\s*', value)
    if m:
        (s1, t1, s2, t2) = m.groups()
        return Duration(units[t1](s1) + units[t2](s2))

    return UNIT_EMPTY

def find_stat(activity, pattern, formatter=identity):
    for stat in activity.select('div.media-body ul.list-stats .stat'):
        m = re.search(pattern, stat.text)
        if m: return formatter(m.group(1))
    return UNIT_EMPTY

class NotLogged(Exception):
    pass

class WrongAuth(Exception):
    pass

class UnexpectedScrapped(Exception):
    def __init__(self, message, content):
        self.message = message
        self.content = content

