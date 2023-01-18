from app import helpers
from datetime import datetime, timedelta

def test_seconds_ago():
    assert helpers.less_than_day(30) == "30 seconds ago"

def test_minute_ago():
    assert helpers.less_than_day(110) == "a minute ago"