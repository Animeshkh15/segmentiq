from collections import Counter
from typing import Optional, Tuple
from app.schemas.schemas import AgentResult, PageClassification, ReviewTask


class VotingEngine:

    def __init__(
        self,
        minimum_successful_agents: int = 3,
        threshold: float = 0.60
    ):
        self.minimum_successful_agents = minimum_successful_agents
        self.threshold = threshold

    def vote(
        self,
        page_number: int,
        results: list[AgentResult]
    ) -> Tuple[PageClassification, Optional[ReviewTask]]:

        successful_results = [
            result
            for result in results
            if result.success and result.category is not None
        ]

        agent_votes = [res.category for res in successful_results]

        if len(successful_results) < self.minimum_successful_agents:
            reason = "Insufficient successful agent responses"
            classification = PageClassification(
                page_number=page_number,
                category="Unknown",
                confidence=0.0,
                reasoning=reason,
                review_required=True
            )
            review_task = ReviewTask(
                page_number=page_number,
                reason=reason,
                confidence=0.0,
                agent_votes=agent_votes,
                winning_category="Unknown",
                reasoning=reason
            )
            return classification, review_task

        counter = Counter(agent_votes)
        winning_category, winning_votes = counter.most_common(1)[0]
        confidence = winning_votes / len(successful_results)

        majority_reasoning = next(
            result.reasoning
            for result in successful_results
            if result.category == winning_category
        ) or f"Classified as {winning_category}"

        if confidence < self.threshold:
            reason = f"Low confidence: {confidence:.2f}"
            reasoning_msg = "Agents produced conflicting classifications."
            classification = PageClassification(
                page_number=page_number,
                category=winning_category,
                confidence=confidence,
                reasoning=reasoning_msg,
                review_required=True
            )
            review_task = ReviewTask(
                page_number=page_number,
                reason=reason,
                confidence=confidence,
                agent_votes=agent_votes,
                winning_category=winning_category,
                reasoning=reasoning_msg
            )
            return classification, review_task

        classification = PageClassification(
            page_number=page_number,
            category=winning_category,
            confidence=confidence,
            reasoning=majority_reasoning,
            review_required=False
        )
        return classification, None