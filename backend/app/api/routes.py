from fastapi import APIRouter

from app.pipeline.document_pipeline import DocumentPipeline
from app.schemas.schemas import ClassificationRequest

router = APIRouter()


@router.get("/health")
def health():

    return {
        "status": "healthy"
    }


@router.post("/classify")
def classify_document(
    request: ClassificationRequest
):

    pipeline = DocumentPipeline()

    results = pipeline.process_document(
        pages=request.pages,
        document_name="classified.pdf"
    )

    return results