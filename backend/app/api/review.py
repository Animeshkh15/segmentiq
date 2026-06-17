import os
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from app.core.review_manager import ReviewManager
from app.schemas.schemas import ReviewTask
from app.exporters.json_exporter import JSONExporter
from app.exporters.excel_exporter import ExcelExporter

router = APIRouter()
review_manager = ReviewManager()


class ResolveReviewRequest(BaseModel):
    document_name: str
    page_number: int
    final_category: str


@router.get("/review/queue", response_model=List[ReviewTask])
def get_review_queue():
    """
    Get all page-level classifications pending human review.
    """
    return review_manager.get_reviews()


@router.post("/review/resolve")
def resolve_review(request: ResolveReviewRequest):
    """
    Resolve a human review task by providing a manual category override.
    Re-runs boundary/segmentation logic and updates stored files.
    """
    # 1. Resolve in memory queue
    resolved = review_manager.resolve_review(request.page_number)

    # 2. Update the stored document data
    filename_base = os.path.splitext(request.document_name)[0]
    json_path = f"storage/{filename_base}_segmented.json"

    if not os.path.exists(json_path):
        raise HTTPException(
            status_code=404,
            detail=f"Document results for {request.document_name} not found on disk."
        )

    try:
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error reading results: {str(e)}"
        )

    # Find and update the page classification
    page_found = False
    for page in data.get("page_results", []):
        if page.get("page_number") == request.page_number:
            page["category"] = request.final_category
            page["review_required"] = False
            page["reasoning"] = "Resolved by human review override."
            page_found = True
            break

    if not page_found:
        raise HTTPException(
            status_code=404,
            detail=f"Page {request.page_number} not found in document results."
        )

    # 3. Re-run segmentation
    page_results = sorted(data["page_results"], key=lambda x: x["page_number"])
    
    segments = []
    segment_id = 1
    current_pages = []
    current_category = None

    def create_segment_dict(seg_id, cat, pages_list):
        # Calculate segment confidence as average
        conf = sum(p["confidence"] for p in page_results if p["page_number"] in pages_list) / len(pages_list)
        # Check if any page in segment still needs review
        review_req = any(p["review_required"] for p in page_results if p["page_number"] in pages_list)
        
        return {
            "seg_obj": {
                "segment_id": seg_id,
                "category": cat,
                "start_page": pages_list[0],
                "end_page": pages_list[-1],
                "pages": pages_list
            },
            "seg_extra": {
                "segment_id": seg_id,
                "category": cat,
                "start_page": pages_list[0],
                "end_page": pages_list[-1],
                "pages": pages_list,
                "confidence": conf,
                "review_required": review_req
            }
        }

    seg_extras = []
    seg_objs = []

    for p_res in page_results:
        p_num = p_res["page_number"]
        p_cat = p_res["category"]
        
        # We start a new segment if it's the first page OR if category changes
        # (Since it's manual override, category boundaries guide the partition)
        if current_category is None or p_cat != current_category:
            if current_pages:
                s_data = create_segment_dict(segment_id, current_category, current_pages)
                seg_objs.append(s_data["seg_obj"])
                seg_extras.append(s_data["seg_extra"])
                segment_id += 1
            current_pages = [p_num]
            current_category = p_cat
        else:
            current_pages.append(p_num)

    if current_pages:
        s_data = create_segment_dict(segment_id, current_category, current_pages)
        seg_objs.append(s_data["seg_obj"])
        seg_extras.append(s_data["seg_extra"])

    # Update segments in data
    data["segments"] = seg_objs

    # 4. Save and re-export
    JSONExporter.export(data, json_path)
    
    excel_path = f"storage/{filename_base}_segmented.xlsx"
    ExcelExporter.export(seg_extras, excel_path)

    return {
        "message": "Review resolved and segmentation updated successfully.",
        "resolved": resolved,
        "results": data
    }
