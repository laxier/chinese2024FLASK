from flask import render_template, flash, redirect, url_for
from app import app
from flask import request
from flask_login import current_user, login_user
from app.forms import LoginForm, RegistrationForm, DeckForm, CardForm, DeleteForm, AddForm
from flask_login import logout_user
from flask_login import login_required
from urllib.parse import urlsplit
import sqlalchemy as sa
from app import db
from datetime import datetime
from app.models import User, Deck, Card, CardPerformance, deck_cards, user_decks


@app.route('/')
@app.route('/index')
@login_required
def index():
    sorted_mydecks = Deck.query \
        .join(user_decks) \
        .filter(user_decks.c.user_id == current_user.id) \
        .order_by(user_decks.c.timestamp.desc()) \
        .limit(4) \
        .all()
    zip_for_decks = zip(sorted_mydecks,
                        [db.session.query(user_decks).filter_by(user_id=current_user.id,
                                                                deck_id=element.id).first().timestamp
                         for element in sorted_mydecks])

    perform = CardPerformance.query \
        .filter_by(user_id=current_user.id) \
        .order_by(CardPerformance.timestamp.desc()).limit(5).all()
    result_zip = zip(perform, [Card.query.get_or_404(element.card_id) for element in perform])
    return render_template("index.html", title='Home Page', decks=sorted_mydecks, zip2=zip_for_decks, zip=result_zip)


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
def my_decks():
    sorted_mydecks = Deck.query \
        .join(user_decks) \
        .filter(user_decks.c.user_id == current_user.id) \
        .order_by(user_decks.c.timestamp.desc()) \
        .all()
    form = DeckForm()
    if form.validate_on_submit():
        new_deck = Deck(name=form.name.data, creator=current_user)
        new_deck.users.add(current_user)
        db.session.add(new_deck)
        db.session.commit()
    return render_template("sets.html", title='My sets', decks=sorted_mydecks, form=form)


@app.route('/deck/<int:id>')
@login_required
def deck(id):
    deck_curr = Deck.query.get_or_404(id)
    words = Card.query \
        .join(deck_cards) \
        .filter(deck_cards.c.deck_id == deck_curr.id) \
        .order_by(deck_cards.c.timestamp) \
        .all()
    result_zip = zip(words,
                     [db.session.query(CardPerformance).filter_by(user_id=current_user.id, card_id=element.id).first()
                      for element in words])
    return render_template("deck.html", title=f"Deck {deck_curr.name}", deck=deck_curr, zip=result_zip)


@app.route('/remove_deck/<int:id>')
@login_required
def remove_deck(id):
    deck_curr = Deck.query.get_or_404(id)
    if current_user.id == deck_curr.creator.id:
        flash(f"Вы создатель колоды {deck_curr.name}. Удалить ее навсегда можно через меню изменить")
    else:
        current_user.decks.remove(deck_curr)
        flash(f"Колода {deck_curr.name} успешно удалена")
    return redirect('/decks')


@app.route('/edit_deck/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_deck(id):
    to_edit = Deck.query.get_or_404(id)
    words = Card.query \
        .join(deck_cards) \
        .filter(deck_cards.c.deck_id == to_edit.id) \
        .order_by(deck_cards.c.timestamp) \
        .all()

    result_zip = zip(words,
                     [db.session.query(CardPerformance).filter_by(user_id=current_user.id, card_id=element.id).first()
                      for element in words])

    form = CardForm()
    form2 = DeleteForm()
    form3 = AddForm()
    if form.validate_on_submit():
        if to_edit.creator_id == current_user.id or current_user.username == 'admin':
            card = Card.query.filter_by(chinese=form.char.data).first()
            if card:
                if card in to_edit.cards:
                    flash('Card already exists')
                    return redirect(f'/edit_deck/{id}')
            else:
                card = Card(chinese=form.char.data)
                db.session.add(card)
                db.session.commit()
                flash('You have created the card')
            to_edit.cards.add(card)
            perform = CardPerformance(user=current_user, card=card)
            db.session.add(perform)
            db.session.commit()
            flash('You have added the card')
            return redirect(f'/edit_deck/{id}')
        else:
            return "Action is not allowed"
    if form2.validate_on_submit():
        if to_edit.creator_id == current_user.id or current_user.username == 'admin':
            db.session.delete(to_edit)
            db.session.commit()
            flash("Deck was deleted")
            return redirect('/decks')
        else:
            return "Action is not allowed"
    if form3.validate_on_submit():
        if to_edit.creator_id == current_user.id or current_user.username == 'admin':
            words = form3.text.data.replace(" ", "").replace("\u200b", "").split("\r\n")
            words_count = 0
            added_count = 0
            exists_count = 0
            created_count = 0
            err_count = 0
            for word in words:
                if word:
                    try:
                        card = Card.query.filter_by(chinese=word).first()
                        if card:
                            if card in to_edit.cards:
                                exists_count += 1
                        else:
                            card = Card(chinese=word)
                            db.session.add(card)
                            db.session.commit()
                            created_count += 1
                        to_edit.cards.add(card)
                        perform = CardPerformance(user=current_user, card=card)
                        db.session.add(perform)
                        db.session.commit()
                        added_count += 1
                    except Exception as e:
                        print(e)
                        err_count += 1
                    words_count += 1

            flash(
                f"{words_count} words; added {added_count}; Created {created_count} cards; Already exists {exists_count}; {err_count} errors")
            return redirect(f'/edit_deck/{id}')
        else:
            return "Action is not allowed"
    return render_template("edit_deck.html", title=f"Deck {to_edit.name}", deck=to_edit, zip=result_zip,
                           form=form, delete_form=form2, add_form=form3)


@app.route('/delete_from_deck/<int:deck_id>/<int:card_id>', methods=['GET', 'POST'])
@login_required
def delete_card_from_deck(deck_id, card_id):
    deck = Deck.query.get_or_404(deck_id)
    card = Card.query.get_or_404(card_id)

    if deck is None or card is None:
        return "Deck or card not found."
    if card in deck.cards:
        deck.cards.remove(card)
        db.session.commit()
        flash("Card successfully deleted from the deck.")
        return redirect(f'/edit_deck/{deck_id}')
    else:
        return "Card is not in the deck."


@app.route('/perf_update/<int:deck_id>/<int:id>/<string:point>')
@login_required
def min_rep(deck_id, id, point):
    performance = CardPerformance.query.get_or_404(id)
    if performance is not None:
        if point == "right":
            performance.right = performance.right + 1
            performance.repetitions = performance.repetitions + 1
            performance.timestamp = datetime.utcnow()
        elif point == "wrong":
            performance.repetitions = performance.repetitions + 1
            performance.timestamp = datetime.utcnow()
        elif point == "null":
            performance.repetitions = 0
            performance.right = 0
            performance.timestamp = datetime.utcnow()
        else:
            return "Error"
        db.session.commit()
        return redirect(f'/edit_deck/{deck_id}')


@app.route('/<string:back>/null/<int:id>')
@login_required
def obnulit(id, back):
    performance = CardPerformance.query.get_or_404(id)
    if performance is not None:
        performance.right = 0
        performance.repetitions = 0
        performance.timestamp = datetime.utcnow()
        db.session.commit()
    else:
        return "Error"
    return redirect(f"/{back}")


@app.route('/delete_card/<int:id>')
@login_required
def delete_card(id):
    if current_user.username == "admin":
        to_delete = Card.query.get_or_404(id)
        if to_delete:
            for performance in to_delete.card_performance:
                db.session.delete(performance)
        db.session.delete(to_delete)
        db.session.commit()
    else:
        return "Недостаточно прав"
    return redirect("/words")


@app.route('/words')
@login_required
def all_words():
    if current_user.username == "admin":
        cards = Card.query.all()
        result_zip = zip(cards, cards)
        return render_template("words.html", title="Все слова", zip=result_zip)
    else:
        perform = CardPerformance.query \
                      .filter_by(user_id=current_user.id) \
                      .order_by(CardPerformance.timestamp.desc()).all()[::-1]
        result_zip = zip(perform, [Card.query.get_or_404(element.card_id) for element in perform])
        return render_template("words.html", title="Все слова", zip=result_zip)
