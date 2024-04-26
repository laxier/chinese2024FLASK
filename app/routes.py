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
from chinese_tools import searchWord, decomposeWord
from flask import jsonify, abort


@app.route('/')
@app.route('/index')
@login_required
def index():
    perform = CardPerformance.query \
        .filter_by(user_id=current_user.id) \
        .order_by(CardPerformance.timestamp.desc()).limit(5).all()
    return render_template("index.html", title='Home Page', perform=perform,
                           now=datetime.utcnow())


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


@app.route('/user/<string:id_or_name>', methods=['GET', 'POST'])
def userpage(id_or_name):
    if id_or_name.isdigit():
        user = User.query.get_or_404(id_or_name)
        form = DeckForm()
        if form.validate_on_submit():
            new_deck = Deck(name=form.name.data, creator=current_user)
            db.session.add(new_deck)
            db.session.commit()
            flash("Deck was created")
            return redirect(f'/user/{user.id}')
        return render_template("userpage.html", title=f"User {user.username}", user=user, form=form)
    else:
        user = User.query.filter_by(username=id_or_name).first()
        return redirect(f'/user/{user.id}')


@app.route('/deck/<int:id>')
def deck(id):
    deck_curr = Deck.query.get_or_404(id)
    # дописать для анонимного пользователя
    return render_template("deck.html", title=f"Deck {deck_curr.name}", deck=deck_curr)


@app.route('/remove_deck/<int:id>')
@login_required
def remove_deck(id):
    deck_curr = Deck.query.get_or_404(id)
    if current_user.id == deck_curr.creator.id:
        flash(f"Вы создатель колоды {deck_curr.name}. Удалить ее навсегда можно через меню изменить")
    else:
        current_user.decks.remove(deck_curr)
        db.session.commit()
        flash(f"Колода {deck_curr.name} успешно удалена")
    return redirect(f'/user/{current_user.id}')


@app.route('/edit_deck/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_deck(id):
    to_edit = Deck.query.get_or_404(id)
    form = CardForm()
    form2 = DeleteForm()
    form3 = AddForm()
    if form.validate_on_submit():
        if to_edit.creator_id == current_user.id or current_user.username == 'admin':
            card = Card.query.filter_by(chinese=form.char.data.replace(u"\u200b", "")).first()
            if card:
                if card in to_edit.cards:
                    flash('Card already exists')
                else:
                    card.create_rel(user=current_user)
                    to_edit.cards.add(card)
                    flash('Card added')
            else:
                card = Card(chinese=form.char.data.replace(u"\u200b", ""))
                db.session.add(card)
                card.create_rel(user=current_user)
                to_edit.cards.add(card)
                flash('Created and Added the Card')
            db.session.commit()
            return redirect(f'/edit_deck/{id}')
        else:
            return "Action is not allowed"

    if form2.validate_on_submit():
        if to_edit.creator_id == current_user.id or current_user.username == 'admin':
            db.session.delete(to_edit)
            db.session.commit()
            flash("Deck was deleted")
            return redirect(f'/user/{current_user.id}')
        else:
            return "Action is not allowed"
    if form3.validate_on_submit():
        if to_edit.creator_id == current_user.id or current_user.username == 'admin':
            words = form3.text.data.replace(" ", "").replace(u"\u200b", "").split("\r\n")
            dictionary = dict()
            for word in words:
                try:
                    card = Card.query.filter_by(chinese=word).first()
                    if card:
                        if card in to_edit.cards:
                            dictionary[word] = 'Card already exists'
                        else:
                            card.create_rel(user=current_user)
                            to_edit.cards.add(card)
                            dictionary[word] = 'Card added'
                    else:
                        card = Card(chinese=word)
                        db.session.add(card)
                        card.create_rel(user=current_user)
                        to_edit.cards.add(card)
                        dictionary[word] = 'Card Created and Added'
                    db.session.commit()
                except Exception as e:
                    dictionary[word] = e
            return render_template("edit_deck.html", title=f"Deck {to_edit.name}", deck=to_edit,
                                   form=form, delete_form=form2, add_form=form3, log_table=dictionary)
        else:
            return "Action is not allowed"
    return render_template("edit_deck.html", title=f"Deck {to_edit.name}", deck=to_edit,
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


@app.route('/add_deck/<int:deck_id>')
@login_required
def add_deck(deck_id):
    deck = Deck.query.get_or_404(deck_id)
    if deck is None:
        return "Deck is not found."
    if deck in current_user.decks:
        flash("Deck is already added")
        return redirect(f'/deck/{deck_id}')
    else:

        deck.add_to_user(current_user)
        db.session.commit()
        flash("Deck successfully added")
        return redirect(f'/deck/{deck_id}')


@app.route('/words')
def all_words():
    cards = Card.query.all()
    return render_template("words.html", title="Все слова", words=cards)


@app.route('/words/retry')
@login_required
def try_words():
    cards = Card.query.all()
    for card in cards:
        if (card.translation == None or card.transcription == None):
            try:
                card.transcription, card.translation = searchWord(card.chinese)
                db.session.commit()
                flash(f"Заново поиск слова {card.chinese}, успех")
            except Exception as e:
                flash(f"Заново поиск слова {card.chinese}, {str(e)}")
    return render_template("words.html", title="Все слова", words=cards)


@app.route('/<string:back>/get_childs/<int:id>')
@login_required
def get_childs(id, back):
    if current_user.username == "admin":
        card = Card.query.get_or_404(id)
        flash(card.children_poisk())
        db.session.commit()
        return redirect(f"/{back}")
    else:
        return "Недостаточно прав"


@app.route('/api/<string:type>/<int:deck_id>/<int:user_id>')
def api(type, deck_id, user_id):
    if type == "deck":
        deck = Deck.query.get_or_404(deck_id)
        cards = [card.to_dict() for card in deck.sort_timestamp_by_user(user_id)]
        return jsonify(cards)
    if type == "deck_user_time":
        deck = Deck.query.get_or_404(deck_id)
        cards = [card.to_dict() for card in deck.sort_timestamp_by_user(user_id)]
        return jsonify(cards)
    if type == "deck_user_performance":
        deck = Deck.query.get_or_404(deck_id)
        cards = [card.to_dict() for card in deck.sort_perf_by_user(user_id)]
        return jsonify(cards)


@app.route('/test/<int:id>')
def test(id):
    deck_curr = Deck.query.get_or_404(id)
    return render_template("test.html", title=f"Deck {deck_curr.name}", deck=deck_curr)


@app.route('/api/update-performance', methods=['POST'])
@login_required
def update_performance():
    data = request.get_json()
    char = data.get('char')
    action = data.get('action')
    if char is None:
        return jsonify({'error': 'Missing character'})
    if action is None:
        return jsonify({'error': 'Missing action'})
    performance = Card.query.filter_by(chinese=char).first().perf_by_user(user_id=current_user.id)
    if performance is None:
        return jsonify({'error': 'Performance not found'})
        print(action)
    if action == "correct":
        performance.correct()
        db.session.commit()
        return jsonify({'message': '+1 repetition processed successfully'})
    if action == "incorrect":
        performance.incorrect()
        db.session.commit()
        return jsonify({'message': '-1 repetition processed successfully'})
    else:
        return jsonify({'error': 'Unknown key'})
