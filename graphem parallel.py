from app import app, db
from app.models import Deck, character
import threading
# requires selenium==4.20.0
MAX_THREADS = 10
semaphore = threading.Semaphore(MAX_THREADS)


def process_element(element):
    with app.app_context():
        temp = character.query.filter_by(chinese=element).first()
        if temp is None:
            temp = character(chinese=element)
            db.session.add(temp)
            temp.get_childs()
            db.session.commit()
            print(element, "created", temp.children)
        else:
            if len(temp.children)>0:
                print(element, "already exists", temp.children)
            else:
                temp.get_childs()
                db.session.commit()
                print(element, "added", temp.children)

def process_card_thread(card):
    for element in card.chinese:
        process_element(element)

def main():
    with app.app_context():
        try:
            deck = Deck.query.get_or_404(7)
            print([card.chinese for card in deck.cards])
            threads = []
            for card in deck.cards:
                thread = threading.Thread(target=process_card_thread, args=(card,))
                thread.start()
                threads.append(thread)
                if len(threads) >= MAX_THREADS:
                    for t in threads:
                        t.join()
                    threads = []
            for thread in threads:
                thread.join()
        finally:
            db.session.close()

if __name__ == "__main__":
    main()
