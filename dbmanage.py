from app import app, db
from app.models import CardPerformance


def main():
    with app.app_context():
        try:
            # Получаем все объекты CardPerformance из базы данных
            card_performances = CardPerformance.query.all()

            for card_performance in card_performances:
                # Определяем количество правильных и неправильных повторений
                num_correct = card_performance.right
                num_wrong = card_performance.wrong

                # Создаем список повторений на основе этих данных
                repetitions = [(True, 5)] * num_correct + [(False, 2)] * num_wrong

                # Моделируем повторения
                card_performance.simulate_repetitions(repetitions)

            # Сохраняем изменения в базе данных после всех операций
            db.session.commit()

            # Выводим результаты для всех объектов
            for card_performance in card_performances:
                print(f'CardPerformance ID: {card_performance.id}')
                print(f'Repetitions: {card_performance.repetitions}')
                print(f'Right: {card_performance.right}')
                print(f'Wrong: {card_performance.wrong}')
                print('---')
        finally:
            db.session.close()

if __name__ == "__main__":
    main()
