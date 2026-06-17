from typing import List
from app.schemas.schemas import ReviewTask


class ReviewManager:
    _review_queue: List[ReviewTask] = []

    def __init__(self):
        pass

    def submit_review(
        self,
        review: ReviewTask
    ):
        # Prevent duplicates
        for existing in self._review_queue:
            if existing.page_number == review.page_number:
                return
        self._review_queue.append(review)

    def get_reviews(self) -> List[ReviewTask]:
        return self._review_queue

    def clear_reviews(self):
        self._review_queue.clear()

    def resolve_review(
        self,
        page_number: int
    ) -> bool:
        for task in self._review_queue:
            if task.page_number == page_number:
                self._review_queue.remove(task)
                return True
        return False