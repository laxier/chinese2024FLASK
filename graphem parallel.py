from app import app, db
from app.models import Deck, character
import threading
from sqlalchemy import exc
from tqdm import tqdm
from chinese_tools import searchWord, decomposeWord
# requires selenium==4.20.0
MAX_THREADS = 5
semaphore = threading.Semaphore(MAX_THREADS)
id = 34

def process_element(element):
    with app.app_context():
        temp = character.query.filter_by(chinese=element).first()
        if temp is None:
            try:
                temp = character(chinese=element)
                db.session.add(temp)
                temp.get_childs()
                db.session.commit()
                print(element, "created", temp.children)
            except exc.IntegrityError:
                print("IntegrityError обработана")
                db.session.rollback()
                temp = character.query.filter_by(chinese=element).first()
                temp.get_childs()
                db.session.commit()
        else:
            if len(temp.children)>0:
                print(element, "already exists", temp.children)
            else:
                temp.get_childs()
                db.session.commit()
                print(element, "added", temp.children)

def process_card_thread(card, pbar):
    for element in card.chinese:
        process_element(element)
    pbar.update(1)

def main():
    with app.app_context():
        try:
            deck = Deck.query.get_or_404(id)
            print([card.chinese for card in deck.cards])
            pbar = tqdm(total=len(deck.cards), desc="Processing deck", unit="card")  # Создаем прогресс-бар
            threads = []
            for card in deck.cards:
                thread = threading.Thread(target=process_card_thread, args=(card, pbar))
                thread.start()
                threads.append(thread)
                if len(threads) >= MAX_THREADS:
                    for t in threads:
                        t.join()
                    threads = []
            for thread in threads:
                thread.join()
            pbar.close()
        finally:
            db.session.close()

if __name__ == "__main__":
    main()

# print(decomposeWord("同"))