from datetime import datetime
import requests
from flask_login import UserMixin
import json
import markdown
import os

from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login
from app.helpers import pretty_date

user_vote = db.Table(
    "user_vote",
    db.Column("user.id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("post.id", db.Integer, db.ForeignKey("post.id"), primary_key=True),
)

comment_vote = db.Table(
    "comment_vote",
    db.Column("user.id", db.Integer, db.ForeignKey("user.id"), primary_key=True),
    db.Column("comment.id", db.Integer, db.ForeignKey("comment.id"), primary_key=True),
)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    posts = db.relationship(
        "Post", order_by="desc(Post.timestamp)", backref="author", lazy="dynamic"
    )
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    post_votes = db.relationship(
        "Post", secondary=user_vote, back_populates="user_votes"
    )
    comments = db.relationship(
        "Comment",
        order_by="desc(Comment.timestamp)",
        backref="author",
        lazy="dynamic"
    )
    comment_votes = db.relationship(
        "Comment", secondary=comment_vote, back_populates="user_votes"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User id {self.id} - {self.username}>"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256))
    body = db.Column(db.Text)
    link = db.Column(db.Boolean, default=False)
    url = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    vote_count = db.Column(db.Integer, default=0)
    user_votes = db.relationship(
        "User", secondary=user_vote, back_populates="post_votes"
    )
    comments = db.relationship(
        "Comment", order_by="desc(Comment.timestamp)", back_populates="post"
    )

    def __repr__(self):
        return f"<Post id {self.id} - {self.title}>" # pragma: no cover

    @classmethod
    def recent_posts(cls):
        return cls.query.order_by(Post.timestamp.desc())

    def body_as_html(self):
        if not self.body:
            return None
        return markdown.markdown(self.body)

    def pretty_timestamp(self):
        return pretty_date(self.timestamp)

    def already_voted(self, user):
        return user in self.user_votes

    def adjust_vote(self, amount):
        if self.vote_count is None:
            self.vote_count = 0
        self.vote_count += amount
        db.session.add(self)

    def up_vote(self, user):
        if self.already_voted(user):
            return
        self.user_votes.append(user)
        self.adjust_vote(1)
        db.session.commit()

    def down_vote(self, user):
        if self.already_voted(user):
            return
        self.user_votes.append(user)
        self.adjust_vote(-1)
        db.session.commit()

    def add_comment(self, comment, user):
        comment = Comment(body=comment,
                          user_id=user.id)
        self.comments.append(comment)
        db.session.commit()
        comment.up_vote(user)
        return comment

    def comment_count(self):
        return len(self.comments)


class Category(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), index=True, unique=True)
    posts = db.relationship(
        "Post", order_by="desc(Post.timestamp)", backref="category", lazy="dynamic"
    )


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"))
    post = db.relationship("Post", back_populates="comments")
    vote_count = db.Column(db.Integer, default=0)
    user_votes = db.relationship(
        "User", secondary=comment_vote, back_populates="comment_votes"
    )

    def __repr__(self):
        return f"<Comment id {self.id} - {self.body[:20]}>" # pragma: no cover

    def pretty_timestamp(self):
        return pretty_date(self.timestamp)

    def already_voted(self, user):
        return user in self.user_votes

    def adjust_vote(self, amount):
        if self.vote_count is None:
            self.vote_count = 0
        self.vote_count += amount
        db.session.add(self)

    def up_vote(self, user):
        if self.already_voted(user):
            return
        self.user_votes.append(user)
        self.adjust_vote(1)
        db.session.commit()

    def down_vote(self, user):
        if self.already_voted(user):
            return
        self.user_votes.append(user)
        self.adjust_vote(-1)
        db.session.commit()


class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    details = db.Column(db.Text)

    def __repr__(self):
        return f"<ActivityLog id {self.id} - {self.details[:20]}>" # pragma: no cover

    @classmethod
    def latest_entry(cls):
        log_url = os.environ.get("LOG_URL")
        get_url = log_url + "/api/activities"
        try:
            r = requests.get(get_url)
            if r.status_code == 200:
                print(f"Get activities SUCCESS at {get_url}")
                activities = json.loads(r.text)
                single_activity_id = 0
                if isinstance(activities, dict):
                    if "activities" in activities:
                        single_activity_id = activities["activities"][0]["id"]
                    else:
                        print("Error: JSON did not have a top level element: activities")
                else:
                    print("Error: JSON returned not a dictionary")
                r = requests.get(f"{get_url}/{single_activity_id}")
                if r.status_code == 200:
                    print(f"    Get single activity {single_activity_id} SUCCESS")
                    print(json.loads(r.text))
                    return json.loads(r.text)
                else:
                    print(f"Get single activity FAILURE: {r.text}")
            else:
                print(f"Get activities FAILURE: {r.text}")
        except requests.exceptions.RequestException:
            print(f"Could not connect to activity log service at {url}")

    @classmethod
    def log_event(cls, user_id, details):
        log_url = os.environ.get("LOG_URL")
        u = user_id
        d = details
        post_url = log_url + "/api/activities"
        new_activity = {
            "user_id": u,
            "username": "bfin",
            "timestamp": str(datetime.utcnow()),
            "details": d,
        }
        try:
            r = requests.post(post_url, json=new_activity)
            if r.status_code == 201:
                print(f"Post new activity SUCCESS at {post_url}")
                print(r.text)
                print(json.loads(r.text))
            else:
                print(f"Post new activity FAILURE: {r.text}")
        except requests.exceptions.RequestException:
            print(f"Could not connect to activity log service at {url}")


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) # pragma: no cover
