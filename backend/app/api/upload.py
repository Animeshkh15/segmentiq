import os
from fastapi import APIRouter
from fastapi import UploadFile
from fastapi import File

from app.core.ocr import OCRService
from app.pipeline.document_pipeline import DocumentPipeline

router = APIRouter()

ocr = OCRService()


@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...)
):

    os.makedirs("storage", exist_ok=True)
    file_path = f"storage/{file.filename}"

    with open(
        file_path,
        "wb"
    ) as buffer:

        buffer.write(
            await file.read()
        )

    pages = ocr.extract_text(
        file_path
    )

    pipeline = DocumentPipeline()

    results = pipeline.process_document(
        pages=pages,
        document_name=file.filename
    )

    return results