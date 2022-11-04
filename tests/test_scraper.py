import pytest, os
import pathlib
import requests
import requests_mock

from stravatools.scraper import StravaScraper

DATA = pathlib.Path(os.path.dirname(os.path.abspath(__file__))) / 'data'


def mock_strava(method, urlpath, filename):
    with open(DATA / 'mock/responses' / filename, 'r') as file:
        method('https://www.strava.com' + urlpath, text=file.read())


def test_login():
    scraper = StravaScraper(pathlib.Path('/tmp/'), '123456')

    with requests_mock.mock() as m:
        mock_strava(m.get, '/login', 'login.html')
        mock_strava(m.post, '/session', 'session-successful.html')
        mock_strava(m.get, '/dashboard/following/31', 'dashboard.html')

        scraper.login('username', 'password')

        assert scraper.owner == ('123456', 'John Smith')
