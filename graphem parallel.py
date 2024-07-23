from app import app, db
from app.models import Deck, character
import threading
from sqlalchemy import exc
from tqdm import tqdm
from chinese_tools import searchWord, decomposeWord
# requires selenium==4.20.0
MAX_THREADS = 5
semaphore = threading.Semaphore(MAX_THREADS)
id = 42


def main():
    with app.app_context():
        try:
            deck = Deck.query.get_or_404(id)

            # Pre-filter characters that need processing
            characters_to_process = set()
            for card in deck.cards:
                for element in card.chinese:
                    temp = character.query.filter_by(chinese=element).first()
                    if temp is None or not temp.children:
                        characters_to_process.add(element)

            print(f"Characters to process: {characters_to_process}")

            pbar = tqdm(total=len(characters_to_process), desc="Processing characters", unit="char")
            threads = []
            for element in characters_to_process:
                thread = threading.Thread(target=process_element_thread, args=(element, pbar))
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


def process_element_thread(element, pbar):
    process_element(element)
    pbar.update(1)


# Modify process_element to remove the filtering logic
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
            temp.get_childs()
            db.session.commit()
            print(element, "updated", temp.children)

if __name__ == "__main__":
    main()

# print(decomposeWord("同"))