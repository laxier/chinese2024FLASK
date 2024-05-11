from flask import render_template, flash, redirect, url_for
from app import app
from flask import request
from flask_login import current_user, login_user
from app.forms import LoginForm, RegistrationForm, DeckForm, CardForm, DeleteForm, AddForm, GraphemaForm
from flask_login import logout_user
from flask_login import login_required
from urllib.parse import urlsplit
import sqlalchemy as sa
from app import db
from datetime import datetime, timezone
from app.models import User, Deck, Card, CardPerformance, user_decks, DeckPerformance, character
from chinese_tools import searchWord
from flask import jsonify
import calendar


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
            card = Card.query.filter_by(
                chinese=form.char.data.replace(" ", "").replace(u"\u00A0", "").replace(u"\u200b", "")).first()
            if card:
                if card in to_edit.cards:
                    flash('Card already exists')
                else:
                    card.create_rel(user=current_user)
                    to_edit.cards.add(card)
                    flash('Card added')
            else:
                card = Card(chinese=form.char.data.replace(" ", "").replace(u"\u00A0", "").replace(u"\u200b", ""))
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
            deckperf = DeckPerformance.query.filter_by(deck_id=to_edit.id).all()
            for entry in deckperf:
                db.session.delete(entry)
            db.session.delete(to_edit)
            db.session.commit()
            flash("Deck was deleted")
            return redirect(f'/user/{current_user.id}')
        else:
            return "Action is not allowed"
    if form3.validate_on_submit():
        if to_edit.creator_id == current_user.id or current_user.username == 'admin':
            words = form3.text.data.replace(" ", "").replace(u"\u00A0", "").replace(u"\u200b", "").split("\r\n")
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
            parents_copy = set(to_delete.parent)
            for card in parents_copy:
                card.children.remove(to_delete)
            for performance in to_delete.card_performance:
                db.session.delete(performance)
            db.session.delete(to_delete)
            db.session.commit()
        search_query = request.args.get('search', '')
        return redirect(url_for('words', search=search_query))
    else:
        return "Недостаточно прав"


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
def words():
    page = request.args.get('page', 1, type=int)
    words_per_page = 20
    search = request.args.get('search', '').strip()
    if search:
        words = Card.query.filter(
            Card.chinese.ilike(f'%{search}%') |
            Card.translation.ilike(f'%{search}%') |
            Card.transcription.ilike(f'%{search}%')
        ).paginate(page=page, per_page=words_per_page, error_out=False)
    else:
        words = Card.query.paginate(page=page, per_page=words_per_page, error_out=False)
    return render_template('words.html', words=words, search=search)

@app.route("/<string:back>/remove_child/<int:card_id>/<int:parent_id>")
def remove_child(back, card_id, parent_id):
    card = Card.query.get_or_404(card_id)
    parent = Card.query.get_or_404(parent_id)
    parent.children.remove(card)
    db.session.commit()
    flash("Card successfully removed")
    search_query = request.args.get('search', '')
    redirect_url = url_for('words', back=back, search=search_query)
    return redirect(redirect_url)

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


@app.route('/<string:back>/get_childs/<int:id>', methods=['GET', 'POST'])
@login_required
def get_childs(id, back):
    if current_user.username == "admin":
        card = Card.query.get_or_404(id)
        if len(card.chinese) == 1:
            search_query = request.args.get('search', '')
            redirect_url = url_for('get_radicals', back=back, id=id, search=search_query)
            return redirect(redirect_url)
        else:
            children, log = card.children_poisk()
            db.session.commit()
            flash(log)
            search_query = request.args.get('search', '')
            redirect_url = url_for(back, search=search_query)
            return redirect(redirect_url)
    else:
        return "Недостаточно прав"

@app.route('/<string:back>/get_radicals/<int:id>', methods=['GET', 'POST'])
@login_required
def get_radicals(id, back):
    card = Card.query.get_or_404(id)
    children, log = card.children_poisk()
    if len(children) == 1:
        flash("Данное слово не поддерживается")
        search_query = request.args.get('search', '')
        redirect_url = url_for(back, search=search_query)
        return redirect(redirect_url)
    form = GraphemaForm()
    form.graphems.choices = [(char.id, char.chinese) for char in children[1]]
    selected_childs = [child.chinese for child in card.children]

    if form.validate_on_submit():
        log = f"{card.chinese}"
        for char in form.graphems.data:
            temp = character.query.get_or_404(char)
            children = Card.query.filter_by(chinese=temp.chinese).first()
            if children is None:
                children = Card(chinese=temp.chinese)
                db.session.add(children)
                log += f"created {children.chinese} {children.translation}"
                card.children.append(children)
                db.session.commit()
            else:
                if children in card.children:
                    log += f"already {children.chinese} {children.translation}"
                else:
                    card.children.append(children)
                    db.session.commit()
                    log += f"added {children.chinese} {children.translation}"
        flash(log)
        search_query = request.args.get('search', '')
        redirect_url = url_for(back, search=search_query)
        return redirect(redirect_url)
    return render_template("radicals.html", title=f"Word {card.chinese}", form=form, selected_childs=selected_childs)


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


@app.route('/api/update-deck', methods=['POST'])
@login_required
def update_deck():
    data = request.get_json()
    id = data.get('id')
    percent = data.get('percent')
    incorrect = data.get('incorrect')
    if percent is None:
        return jsonify({'error': 'Missing percent'})
    if id is None:
        return jsonify({'error': 'Missing id'})
    deck_perf = DeckPerformance(user_id=current_user.id, deck_id=id, percent_correct=percent, test_date=datetime.now(),
                                wrong_answers=incorrect)
    db.session.add(deck_perf)
    update_query = user_decks.update().values(percent=percent).where(
        (user_decks.c.user_id == current_user.id) & (user_decks.c.deck_id == id))
    db.session.execute(update_query)
    db.session.commit()
    return jsonify({'message': 'processed successfully'})


def format_date(date):
    day = date.day
    month = date.month
    month_name = calendar.month_name[month]
    formatted_date = f"{day} {month_name.lower()}"
    return formatted_date


@app.route('/get-performance-data/<deck_id>/<user_id>', methods=['GET'])
def get_performance_data(deck_id, user_id):
    data = DeckPerformance.query.filter_by(user_id=user_id, deck_id=deck_id).all()
    performance_data = {
        'dates': [format_date(row.test_date) for row in data],
        'percentages': [row.percent_correct for row in data],
        'wrongAnswers': [row.wrong_answers for row in data]
    }
    return jsonify(performance_data)


if __name__ == '__main__':
    app.run()
