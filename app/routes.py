from flask import render_template, flash, redirect, url_for
from app import app
from flask import request
from flask_login import current_user, login_user
from app.forms import LoginForm, RegistrationForm, DeckForm, CardForm
from flask_login import logout_user
from flask_login import login_required
from urllib.parse import urlsplit
import sqlalchemy as sa
from app import db
from app.models import User, Deck, Card

import os
@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template("index.html", title='Home Page')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/decks', methods=['GET', 'POST'])
@login_required
def deck():
    decks = current_user.decks
    form = DeckForm()
    if form.validate_on_submit():
        deck = Deck(name = form.name.data, creator = current_user)
        deck.users.add(current_user)
        db.session.add(deck)
        db.session.commit()
    return render_template("sets.html", title='My sets', decks=decks, form = form)

@app.route('/edit_deck/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_deck(id):
    to_edit = Deck.query.get_or_404(id)
    form = CardForm()
    if form.validate_on_submit():
        if to_edit.creator_id == current_user.id or current_user.username == 'admin':
            exists = Card.query.filter_by(chinese=form.char.data).first()
            if exists:
                if exists in to_edit.cards:
                    flash('Card already exists')
                    return redirect(f'/edit_deck/{id}')
                to_edit.cards.add(exists)
                db.session.commit()
            else:
                card = Card(chinese = form.char.data)
                db.session.add(card)
                db.session.commit()
                to_edit.cards.add(card)
                db.session.commit()
                flash('You have created the card')
            flash('You have added the card')
            return redirect(f'/edit_deck/{id}')
        else:
            return "Action is not allowed"
    return render_template("edit_deck.html", title=f"Editing {to_edit.name}", deck=to_edit, form=form)

@app.route('/delete_from_deck/<int:deck_id>/<int:card_id>', methods=['GET', 'POST'])
@login_required
def delete_card_from_deck(deck_id, card_id):
    deck = Deck.query.get(deck_id)
    card = Card.query.get(card_id)

    if deck is None or card is None:
        return "Deck or card not found."
    if card in deck.cards:
        deck.cards.remove(card)
        db.session.commit()
        flash("Card successfully deleted from the deck.")
        return redirect(f'/edit_deck/{deck_id}')
    else:
        return "Card is not in the deck."

