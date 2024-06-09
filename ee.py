import math
from datetime import datetime, timedelta, timezone
from typing import List, Tuple


class CardPerformance:
    def __init__(self, user_id: int, card_id: int, ef_factor: float = 2.0):
        self.id = None  # Можно присвоить уникальный идентификатор, если требуется
        self.user_id = user_id
        self.card_id = card_id
        self.ef_factor = ef_factor
        self._minimum_ef_factor = 1.3
        self._maximum_ef_factor = 5.0
        self.repetitions = 0
        self.right = 0
        self.wrong = 0
        self.timestamp = datetime.now(timezone.utc)
        self.edited = datetime.now(timezone.utc)
        self.next_review_date = datetime.now(timezone.utc)

    @property
    def accuracy_percentage(self):
        if self.repetitions > 0:
            return round((self.right / self.repetitions) * 100)
        else:
            return 0

    def calculate_interval(self, repetitions, quality):
        if repetitions == 1:
            interval = 1
        else:
            interval = math.ceil(self.ef_factor * (repetitions - 1))

        if quality < 3:
            interval = 1

        new_ef_factor = self.ef_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        self.ef_factor = max(self._minimum_ef_factor, min(new_ef_factor, self._maximum_ef_factor))

        return interval

    def correct(self):
        self.repetitions += 1
        self.right += 1
        quality = 4

        interval = self.calculate_interval(self.repetitions, quality)
        self.edited = datetime.now(timezone.utc)
        self.next_review_date = datetime.now(timezone.utc) + timedelta(days=interval)

    def incorrect(self):
        self.repetitions += 1
        self.wrong += 1
        quality = 2

        if self.accuracy_percentage >= 80:
            quality = 1

        interval = self.calculate_interval(self.repetitions, quality)
        self.edited = datetime.now(timezone.utc)
        self.next_review_date = datetime.now(timezone.utc) + timedelta(days=interval)

    def simulate_repetitions(self, repetitions: List[Tuple[bool, int]]):
        self.repetitions = 0
        self.right = 0
        self.wrong = 0
        for is_correct, quality in repetitions:
            if is_correct:
                self.repetitions += 1
                self.right += 1
            else:
                self.repetitions += 1
                self.wrong += 1
            new_ef_factor = self.ef_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
            self.ef_factor = max(self._minimum_ef_factor, min(new_ef_factor, self._maximum_ef_factor))
        if repetitions:
            quality = repetitions[-1][1]
            interval = self.calculate_interval(self.repetitions, quality)
            self.next_review_date = self.edited + timedelta(days=interval)
        else:
            self.ef_factor = 2.0

    def __repr__(self):
        return f'{self.right}/{self.repetitions}'


# Пример использования
card_performance = CardPerformance(user_id=1, card_id=1)
card_performance.timestamp = datetime(2024, 5, 19, 19, 32, 52, tzinfo=timezone.utc)
card_performance.edited = datetime(2024, 6, 9, 9, 20, 37, tzinfo=timezone.utc)
card_performance.next_review_date = datetime(2024, 6, 13, 9, 20, 37, tzinfo=timezone.utc)

print(f"ef_factor: {card_performance.ef_factor}")
print(f"next_review_date: {card_performance.next_review_date}")
print(f"repetitions: {card_performance.repetitions}")
print(f"accuracy_percentage: {card_performance.accuracy_percentage}")

card_performance.incorrect()
print(f"ef_factor: {card_performance.ef_factor}")
print(f"next_review_date: {card_performance.next_review_date}")
print(f"repetitions: {card_performance.repetitions}")
print(f"accuracy_percentage: {card_performance.accuracy_percentage}")

card_performance.incorrect()
print(f"ef_factor: {card_performance.ef_factor}")
print(f"next_review_date: {card_performance.next_review_date}")
print(f"repetitions: {card_performance.repetitions}")
print(f"accuracy_percentage: {card_performance.accuracy_percentage}")

card_performance.incorrect()
print(f"ef_factor: {card_performance.ef_factor}")
print(f"next_review_date: {card_performance.next_review_date}")
print(f"repetitions: {card_performance.repetitions}")
print(f"accuracy_percentage: {card_performance.accuracy_percentage}")

card_performance.correct()
print(f"ef_factor: {card_performance.ef_factor}")
print(f"next_review_date: {card_performance.next_review_date}")
print(f"repetitions: {card_performance.repetitions}")
print(f"accuracy_percentage: {card_performance.accuracy_percentage}")
# card_performance.edited = datetime.now(timezone.utc)
# card_performance.next_review_date = datetime.now(timezone.utc) + timedelta(days=interval)
#
# print(f"ef_factor: {card_performance.ef_factor}")
# print(f"next_review_date: {card_performance.next_review_date}")
