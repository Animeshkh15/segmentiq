import os
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()


@router.get("/results/download/{filename}")
def download_file(filename: str):
    """
    Download a generated JSON or Excel file from the storage folder.
    """
    file_path = f"storage/{filename}"

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found in storage."
        )

    media_type = "application/octet-stream"
    if filename.endswith(".json"):
        media_type = "application/json"
    elif filename.endswith(".xlsx"):
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type=media_type
    )
