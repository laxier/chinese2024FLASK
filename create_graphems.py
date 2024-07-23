from app import app, db
from app.models import Deck, character

id = 39


def main():
    with app.app_context():
        try:
            deck = Deck.query.get_or_404(id)
            for card in deck.cards:
                for element in card.chinese:
                    temp = character.query.filter_by(chinese=element).first()
                    if temp is not None:
                        print(temp.chinese, temp.children)
                    else:
                        print(element)
        finally:
            db.session.close()


if __name__ == "__main__":
    main()
