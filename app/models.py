from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from typing import Optional
from datetime import datetime, timezone
from typing import List, Set
import sqlalchemy as sa
import sqlalchemy.orm as so
from chinese_tools import searchWord
from app import db
from app import login


class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True, unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True, unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    decks_created: so.Mapped[Set["Deck"]] = so.relationship(back_populates="creator", cascade="all, delete-orphan",
                                                            passive_deletes=True)
    card_performance: so.Mapped[Set["CardPerformance"]] = so.relationship(back_populates="user",
                                                                          cascade="all, delete-orphan",
                                                                          passive_deletes=True)
    decks: so.Mapped[Set["Deck"]] = so.relationship(secondary='user_decks', back_populates='users')

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Card(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    chinese: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True)
    transcription: so.Mapped[Optional[str]] = so.mapped_column(sa.String(200))
    translation: so.Mapped[Optional[str]] = so.mapped_column(sa.String(200))
    decks: so.Mapped[Set["Deck"]] = so.relationship(secondary='deck_cards', back_populates='cards')
    card_performance: so.Mapped[Set["CardPerformance"]] = so.relationship(back_populates="card",
                                                                          cascade="all, delete-orphan",
                                                                          passive_deletes=True)

    def __init__(self, chinese):
        self.chinese = chinese
        try:
            self.transcription, self.translation = searchWord(chinese)
        except Exception as e:
            print(f"Failed to fetch data for character {chinese}: {Exception}")


class Deck(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100))
    creator_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), nullable=False)
    creator: so.Mapped[User] = so.relationship(back_populates="decks_created")
    users: so.Mapped[Set["User"]] = so.relationship('User', secondary='user_decks', back_populates='decks')
    cards: so.Mapped[Set["Card"]] = so.relationship('Card', secondary='deck_cards', back_populates='decks')


user_decks = db.Table(
    'user_decks',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('deck_id', db.Integer, db.ForeignKey('deck.id')),
    db.Column('timestamp', db.DateTime, server_default=db.func.now())
)

deck_cards = db.Table(
    'deck_cards',
    db.Column('deck_id', db.Integer, db.ForeignKey('deck.id')),
    db.Column('card_id', db.Integer, db.ForeignKey('card.id')),
    db.Column('timestamp', db.DateTime, server_default=db.func.now())
)


class CardPerformance(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    repetitions: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    right: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id, ondelete='CASCADE'), nullable=False)
    user: so.Mapped[User] = so.relationship(back_populates="card_performance")
    timestamp: so.Mapped[datetime] = so.mapped_column(index=True, default=lambda: datetime.now(timezone.utc))
    card_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Card.id, ondelete='CASCADE'), nullable=False)
    card: so.Mapped[Card] = so.relationship(back_populates="card_performance")

    @property
    def accuracy_percentage(self):
        if self.repetitions == 0:
            return 0
        if self.repetitions > 5:
            return round((self.right / self.repetitions) * 100)
        else:
            return round((self.right / 5) * 100)

    def __repr__(self):
        return f'{self.right}/{self.repetitions}'


@login.user_loader
def load_user(id):
    return db.session.query(User).get(id)
