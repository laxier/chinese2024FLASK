from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from typing import Optional
from datetime import datetime, timezone
from typing import Set
import sqlalchemy as sa
from sqlalchemy import exc
import sqlalchemy.orm as so
from chinese_tools import searchWord, decomposeWord
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

    def sort_user_decs(self):
        query = Deck.query \
            .join(user_decks) \
            .filter(user_decks.c.user_id == self.id) \
            .order_by(user_decks.c.timestamp.desc())
        return query.all()

    def sort_user_decs_four(self):
        query = Deck.query \
            .join(user_decks) \
            .filter(user_decks.c.user_id == self.id) \
            .order_by(user_decks.c.edited.desc())
        return query.limit(4).all()


childrens = db.Table(
    'childrens',
    db.Column('parent_id', sa.Integer, sa.ForeignKey('card.id'),
              primary_key=True),
    db.Column('children_id', sa.Integer, sa.ForeignKey('card.id'),
              primary_key=True)
)


class Card(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    chinese: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True)
    transcription: so.Mapped[Optional[str]] = so.mapped_column(sa.String(200))
    translation: so.Mapped[Optional[str]] = so.mapped_column(sa.String(200))
    decks: so.Mapped[Set["Deck"]] = so.relationship(secondary='deck_cards', back_populates='cards')
    card_performance: so.Mapped[Set["CardPerformance"]] = so.relationship(back_populates="card",
                                                                          cascade="all, delete-orphan",
                                                                          passive_deletes=True)
    children: so.Mapped[Set['Card']] = so.relationship(
        secondary=childrens, primaryjoin=(childrens.c.parent_id == id),
        secondaryjoin=(childrens.c.children_id == id),
        back_populates='parent', lazy='dynamic')

    parent: so.Mapped[Set['Card']] = so.relationship(
        secondary=childrens, primaryjoin=(childrens.c.children_id == id),
        secondaryjoin=(childrens.c.parent_id == id),
        back_populates='children')

    def __init__(self, chinese):
        self.chinese = chinese
        try:
            self.transcription, self.translation = searchWord(chinese)
        except Exception as e:
            print(f"Failed to fetch data for character {chinese}: {str(e)}")

    def children_poisk(self):
        log = ""
        if len(self.chinese) > 1:
            for element in self.chinese:
                if element:
                    log += f"\n{element}"
                    query = sa.select(Card).filter_by(chinese=element)
                    element_card = db.session.scalar(query)
                    if element_card not in self.children:
                        if not (element_card):
                            element_card = Card(chinese=element)
                            db.session.add(element_card)
                        self.children.add(element_card)
                        log += " связь создана"
                    else:
                        log += " связь уже существует"
            return [1], log
        else:
            query = sa.select(character).filter_by(chinese=self.chinese)
            new = db.session.scalar(query)
            if new:
                log += new.chinese + " = "
                for child in new.children:
                    log += child.chinese
                return [new, new.children], log
            else:
                return [0], "Данное слово не поддерживается"

    def create_rel(self, user):
        query = sa.select(CardPerformance).filter_by(card_id=self.id, user_id=user.id)
        performance = db.session.execute(query).first()
        if performance:
            return 0
        else:
            performance = CardPerformance(user=user, card=self)
            db.session.add(performance)
            return 0

    def perf_by_user(self, user_id):
        query = sa.select(CardPerformance).filter_by(user_id=user_id, card_id=self.id)
        return db.session.scalar(query)


def __repr__(self):
    return '<Word {}>'.format(self.chinese)


class Deck(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(100))
    creator_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), nullable=False)
    creator: so.Mapped[User] = so.relationship(back_populates="decks_created")
    users: so.Mapped[Set["User"]] = so.relationship('User', secondary='user_decks', back_populates='decks')
    cards: so.Mapped[Set["Card"]] = so.relationship('Card', secondary='deck_cards', back_populates='decks')

    def __init__(self, name, creator):
        self.name = name
        self.creator = creator
        self.users.add(self.creator)

    def timestamp_created(self, user_id):
        query = sa.select(user_decks).filter_by(user_id=user_id, deck_id=self.id)
        return db.session.execute(query).one().timestamp

    def percent_for_user(self, user_id):
        query = sa.select(user_decks).filter_by(user_id=user_id, deck_id=self.id)
        return db.session.execute(query).one().percent

    def edited_by_user(self, user_id):
        query = sa.select(user_decks).filter_by(user_id=user_id, deck_id=self.id)
        return db.session.execute(query).one().edited

    def sort_timestamp_by_user(self, user_id):
        query = sa.select(user_decks).filter_by(user_id=user_id, deck_id=self.id)
        progress = db.session.execute(query).first()
        if progress:
            query = db.session.query(Card).join(Card.card_performance) \
                .filter(CardPerformance.user_id == user_id,
                        CardPerformance.card_id.in_([card.id for card in self.cards])) \
                .order_by(CardPerformance.timestamp)
            return query.all()
        else:
            return self.cards

    def sort_perf_by_user(self, user_id):
        query = sa.select(user_decks).filter_by(user_id=user_id, deck_id=self.id)
        progress = db.session.execute(query).first()
        if progress:
            query = db.session.query(Card).join(Card.card_performance) \
                .filter(CardPerformance.user_id == user_id,
                        CardPerformance.card_id.in_([card.id for card in self.cards])) \
                .order_by(CardPerformance.wrong.desc(), CardPerformance.repetitions)
            return query.all()
        else:
            return self.cards

    def sort_percent_by_user(self, user_id):
        query = sa.select(user_decks).filter_by(user_id=user_id, deck_id=self.id)
        progress = db.session.execute(query).first()
        if progress:
            query = db.session.query(Card).join(Card.card_performance) \
                .filter(CardPerformance.user_id == user_id,
                        CardPerformance.card_id.in_([card.id for card in self.cards]))
            cards = query.all()
            cards.sort(key=lambda card: (card.perf_by_user(user_id).accuracy_percentage,
                                         card.perf_by_user(user_id).repetitions,
                                         -card.perf_by_user(user_id).wrong))
            return cards
        else:
            return self.cards

    def add_to_user(self, user):
        user.decks.add(self)
        for card in self.cards:
            card.create_rel(user)


user_decks = db.Table(
    'user_decks',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('deck_id', db.Integer, db.ForeignKey('deck.id')),
    db.Column('percent', db.Integer, default=0),
    db.Column('timestamp', db.DateTime, default=lambda: datetime.now(timezone.utc)),
    db.Column('edited', db.DateTime, default=lambda: datetime.now(timezone.utc),
              onupdate=lambda: datetime.now(timezone.utc))
)

deck_cards = db.Table(
    'deck_cards',
    db.Column('deck_id', db.Integer, db.ForeignKey('deck.id')),
    db.Column('card_id', db.Integer, db.ForeignKey('card.id')),
    db.Column('timestamp', db.DateTime, default=lambda: datetime.now(timezone.utc))
)


class CardPerformance(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    repetitions: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    right: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
    wrong: so.Mapped[int] = so.mapped_column(sa.Integer, default=0)
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

    def correct(self):
        self.repetitions += 1
        self.right += 1

    def incorrect(self):
        self.repetitions += 1
        self.wrong += 1
        self.timestamp = datetime.now(timezone.utc)

    def __repr__(self):
        return f'{self.right}/{self.repetitions}'


class DeckPerformance(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id), nullable=False)
    deck_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(Deck.id), nullable=False)
    percent_correct: so.Mapped[int] = so.mapped_column(sa.Integer)
    test_date: so.Mapped[datetime] = so.mapped_column(default=datetime.now)
    wrong_answers: so.Mapped[str] = so.mapped_column(sa.Text)

    def __repr__(self):
        return f'Deck Performance: User {self.user_id}, Deck {self.deck_id}, Percent Correct {self.percent_correct}, Test Date {self.test_date}'


character_rel = db.Table(
    'character_rel',
    db.Column('parent_id', sa.Integer, sa.ForeignKey('character.id'),
              primary_key=True),
    db.Column('children_id', sa.Integer, sa.ForeignKey('character.id'),
              primary_key=True)
)


class character(db.Model):
    __tablename__ = 'character'
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    chinese: so.Mapped[str] = so.mapped_column(sa.String(100), unique=True)
    children: so.Mapped[Set['character']] = so.relationship(
        secondary=character_rel, primaryjoin=(character_rel.c.parent_id == id),
        secondaryjoin=(character_rel.c.children_id == id),
        back_populates='parent')

    parent: so.Mapped[Set['character']] = so.relationship(
        secondary=character_rel, primaryjoin=(character_rel.c.children_id == id),
        secondaryjoin=(character_rel.c.parent_id == id),
        back_populates='children')

    def __init__(self, chinese):
        self.chinese = chinese

    def __repr__(self):
        return self.chinese

    def get_childs(self):
        try:
            words = decomposeWord(self.chinese)
            # print(words)
        except Exception as e:
            print(str(e))
            return
        log = f"{self.chinese}\n"
        for element in words[1::]:
            if element:
                log += f"\n{element}"
                query = sa.select(character).filter_by(chinese=element)
                element_card = db.session.scalar(query)
                if element_card:
                    if element_card not in self.children:
                        self.children.add(element_card)
                        db.session.commit()
                        log += " связь добавлена"
                    else:
                        log += " связь уже существует"
                else:
                    try:
                        element_card = character(chinese=element)
                        db.session.add(element_card)
                        db.session.commit()
                    except exc.IntegrityError:
                        print("IntegrityError обработана")
                        db.session.rollback()
                        query = sa.select(character).filter_by(chinese=element)
                        element_card = db.session.scalar(query)
                        self.children.add(element_card)
                        db.session.commit()
                        log += " связь добавлена"
                    else:
                        self.children.add(element_card)
                        db.session.commit()
                        log += " связь создана"
        return log


@login.user_loader
def load_user(id):
    return db.session.query(User).get(id)
