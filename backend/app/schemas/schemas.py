from pydantic import BaseModel
from typing import List, Optional

class OCRPage(BaseModel):
    page_number: int
    text: str


class AgentPrediction(BaseModel):
    page_number: int
    category: str
    reasoning: str

class AgentResult(BaseModel):
    success: bool
    category: Optional[str] = None
    reasoning: Optional[str] = None
    error: Optional[str] = None


class VotingResult(BaseModel):
    page_number: int
    category: str
    confidence: float
    votes: int
    total_agents: int
    reasoning: str


class ReviewTask(BaseModel):
    page_number: int
    reason: str
    confidence: float
    agent_votes: List[str]
    winning_category: str
    reasoning: str


class Segment(BaseModel):
    segment_id: int
    category: str
    start_page: int
    end_page: int
    pages: List[int]


class PageClassification(BaseModel):
    page_number: int
    category: str
    confidence: float
    reasoning: str
    review_required: bool


class PipelineResult(BaseModel):
    document_name: str
    page_results: List[PageClassification]
    segments: List[Segment]


class ProcessingResult(BaseModel):
    segments: List[Segment]


class ReviewRequired(BaseModel):
    page_number: int
    reason: str


class ClassificationRequest(BaseModel):
    pages: dict[int, str]