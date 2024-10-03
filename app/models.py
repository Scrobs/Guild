# app/models.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db

# Association table for votes
votes = db.Table('votes',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('game_id', db.Integer, db.ForeignKey('game.id'), primary_key=True)
)

# Association table for game ownership
user_games = db.Table('user_games',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('game_id', db.Integer, db.ForeignKey('game.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, unique=True)
    bgg_username = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(128), nullable=False)
    votes = db.relationship('Game', secondary=votes, backref=db.backref('voters', lazy='dynamic'), lazy='dynamic')
    owned_games = db.relationship('Game', secondary=user_games, backref=db.backref('owners', lazy='dynamic'), lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def vote_count(self):
        return self.votes.count()

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bgg_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(250), nullable=False)
    thumbnail = db.Column(db.String(500))
    min_players = db.Column(db.Integer)
    max_players = db.Column(db.Integer)
    playing_time = db.Column(db.Integer)
    difficulty = db.Column(db.String(50))

    @property
    def vote_count(self):
        return self.voters.count()
