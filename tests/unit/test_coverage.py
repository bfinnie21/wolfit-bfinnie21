from app import helpers
from datetime import datetime, timedelta

from app import models

from flask import url_for

import pytest

from app import app, db
from app.models import ActivityLog, Category, Comment, Post, User

def test_seconds_ago():
    assert helpers.less_than_day(55) == "55 seconds ago"

def test_minute_ago():
    assert helpers.less_than_day(110) == "a minute ago"

def test_minutes_ago():
    assert helpers.less_than_day(300) == "5 minutes ago"

def test_hour_ago():
    assert helpers.less_than_day(4600) == "an hour ago"

def test_hours_ago():
    assert helpers.less_than_day(60000) == "16 hours ago"

def test_pretty_date_yesterday():
    assert(helpers.pretty_date(datetime.utcnow() - timedelta(days=1))) == "Yesterday"

def test_pretty_date_days_ago():
    assert(helpers.pretty_date(datetime.utcnow() - timedelta(days=3))) == "3 days ago"

def test_pretty_date_weeks_ago():
    assert(helpers.pretty_date(datetime.utcnow() - timedelta(days=27))) == "3 weeks ago"

def test_pretty_date_months_ago():
    assert(helpers.pretty_date(datetime.utcnow() - timedelta(days=90))) == "3 months ago"

def test_pretty_date_years_ago():
    assert(helpers.pretty_date(datetime.utcnow() - timedelta(days=400))) == "1 years ago"

def test_pretty_null():
    assert(helpers.pretty_date()) == "just now"

def test_pretty_passing_int():
    assert(helpers.pretty_date(32)) == "53 years ago"




