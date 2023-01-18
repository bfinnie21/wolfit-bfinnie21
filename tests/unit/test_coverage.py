from app import helpers
from datetime import datetime, timedelta

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