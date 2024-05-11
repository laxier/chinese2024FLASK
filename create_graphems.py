from app import app, db
from app.models import Deck, character

def main():
    with app.app_context():
        try:
            deck = Deck.query.get_or_404(7)
            for card in deck.cards:
                for element in card.chinese:
                    temp = character.query.filter_by(chinese=element).first()
                    print(temp.chinese, temp.children)
        finally:
            db.session.close()


if __name__ == "__main__":
    main()
