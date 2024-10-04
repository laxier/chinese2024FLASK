from app import app, db
from app.models import Deck, character
import threading
from sqlalchemy import exc
from tqdm import tqdm

MAX_THREADS = 5
semaphore = threading.Semaphore(MAX_THREADS)

def main():
    """
    Main function to process decks and characters.

    This function iterates through deck IDs 64 to 74, processes the characters
    in each deck, and keeps track of processed and unprocessed characters and IDs.
    It also writes unprocessed IDs and characters to separate files.
    """
    unprocessed_ids = []
    all_characters_to_process = set()
    successfully_processed_characters = set()
    unprocessed_characters_by_id = {}  # Dictionary to store unprocessed characters by ID

    with app.app_context():
        for id in range(64, 75):  # Process IDs from 64 to 74
            try:
                deck = Deck.query.get(id)
                if deck is None:
                    print(f"No deck found for ID {id}, continuing...")
                    unprocessed_ids.append(id)
                    continue

                characters_to_process = set()
                # Collect characters that need to be processed
                for card in deck.cards:
                    for element in card.chinese:
                        temp = character.query.filter_by(chinese=element).first()
                        if temp is None or not temp.children:
                            characters_to_process.add(element)

                all_characters_to_process.update(characters_to_process)
                print(f"ID {id} - Characters to process: {characters_to_process}")

                pbar = tqdm(total=len(characters_to_process), desc=f"Processing characters for ID {id}", unit="char")
                threads = []
                error_characters = set()  # Set to track characters that encounter errors

                for element in characters_to_process:
                    thread = threading.Thread(target=process_element_thread,
                                              args=(element, pbar, successfully_processed_characters, error_characters))
                    thread.start()
                    threads.append(thread)
                    if len(threads) >= MAX_THREADS:
                        for t in threads:
                            t.join()
                        threads = []
                for thread in threads:
                    thread.join()
                pbar.close()

                # Collect characters that failed to process due to errors
                unprocessed_characters = characters_to_process - successfully_processed_characters - error_characters
                if unprocessed_characters:
                    unprocessed_characters_by_id[id] = unprocessed_characters

            except Exception as e:
                print(f"Error processing ID {id}: {str(e)}")
                unprocessed_ids.append(id)
            finally:
                db.session.close()

    # Write unprocessed IDs to file
    with open("unprocessed_ids.txt", "w") as f:
        for id in unprocessed_ids:
            f.write(f"{id}\n")
    print(f"Unprocessed IDs written to unprocessed_ids.txt")

    # Write unprocessed characters to file
    with open("unprocessed_characters.txt", "w") as f:
        for id, chars in unprocessed_characters_by_id.items():
            f.write(f"Deck ID {id} - Unprocessed Characters: {', '.join(chars)}\n")
    print(f"Unprocessed characters written to unprocessed_characters.txt")
    print(f"Characters left to process: {all_characters_to_process - successfully_processed_characters}")

def process_element_thread(element, pbar, successfully_processed_characters, error_characters):
    """
    Thread function to process a single character element.

    Args:
        element (str): The character to process.
        pbar (tqdm): Progress bar object to update.
        successfully_processed_characters (set): Set to update with successfully processed characters.
        error_characters (set): Set to track characters that encounter errors.
    """
    try:
        if process_element(element):
            successfully_processed_characters.add(element)
    except Exception as e:
        print(f"Error processing element {element}: {str(e)}")
        error_characters.add(element)  # Add to error characters if there's an exception
    finally:
        pbar.update(1)

def process_element(element):
    """
    Process a single character element.

    This function either creates a new character entry or updates an existing one.

    Args:
        element (str): The character to process.

    Returns:
        bool: True if the character was successfully processed, False otherwise.
    """
    with app.app_context():
        temp = character.query.filter_by(chinese=element).first()
        if temp is None:
            try:
                temp = character(chinese=element)
                db.session.add(temp)
                temp.get_childs()
                db.session.commit()
                print(element, "created", temp.children)
                return True
            except exc.IntegrityError:
                print("IntegrityError handled")
                db.session.rollback()
                temp = character.query.filter_by(chinese=element).first()
                temp.get_childs()
                db.session.commit()
                return True
        else:
            temp.get_childs()
            db.session.commit()
            print(element, "updated", temp.children)
            return True
    return False

if __name__ == "__main__":
    main()
