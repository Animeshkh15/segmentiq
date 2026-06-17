import os
import yaml
from typing import Dict, List, Any

from app.core.agent_pool import AgentPool
from app.core.voting import VotingEngine
from app.core.review_manager import ReviewManager
from app.core.boundary import BoundaryDetector
from app.core.ocr import OCRService
from app.schemas.schemas import (
    PageClassification,
    ReviewTask,
    Segment,
    PipelineResult
)
from app.exporters.json_exporter import JSONExporter
from app.exporters.excel_exporter import ExcelExporter


class DocumentPipeline:

    def __init__(self):
        with open("config/config.yaml", "r", encoding="utf-8") as file:
            self.config = yaml.safe_load(file)

        min_agents = self.config["agents"].get("minimum_successful_agents", 3)
        threshold = self.config["review"].get("threshold", 0.60)

        self.agent_pool = AgentPool()
        self.voting_engine = VotingEngine(
            minimum_successful_agents=min_agents,
            threshold=threshold
        )
        self.review_manager = ReviewManager()
        self.boundary_detector = BoundaryDetector()

    def process_document(
        self,
        pages: Dict[int, str],
        document_name: str = "document.pdf"
    ) -> Dict[str, Any]:

        print("Pipeline started")

        page_classifications: Dict[int, PageClassification] = {}
        
        agent_results_output = []

        voting_results_output = []

        # Step 1: Page-level classifications and OCR quality check
        for page_number, text in pages.items():
            print(f"Processing page {page_number}")

            # Check OCR quality
            is_poor, poor_reason = OCRService.assess_quality(text)
            if is_poor:
                print(f"Poor OCR quality detected on Page {page_number}: {poor_reason}")
                classification = PageClassification(
                    page_number=page_number,
                    category="Unknown",
                    confidence=0.0,
                    reasoning=poor_reason,
                    review_required=True
                )
                page_classifications[page_number] = classification

                # Submit to human review
                review_task = ReviewTask(
                    page_number=page_number,
                    reason=poor_reason,
                    confidence=0.0,
                    agent_votes=[],
                    winning_category="Unknown",
                    reasoning=poor_reason
                )
                self.review_manager.submit_review(review_task)
                continue

            # Run multi-agent pool
            agent_results = self.agent_pool.classify_page(
                page_number=page_number,
                text=text
            )
            page_agent_data = {
                "page_number": page_number,
                "agents": []
            }

            for idx, agent_result in enumerate(agent_results, start=1):

                page_agent_data["agents"].append({
                    "agent_id": idx,
                    "success": agent_result.success,
                    "category": getattr(agent_result, "category", None),
                    "reasoning": getattr(agent_result, "reasoning", None),
                    "error": getattr(agent_result, "error", None)
                })

            agent_results_output.append(
                page_agent_data
            )

            print(f"Agent results received for page {page_number}")

            # Voting & confidence scoring
            classification, review_task = self.voting_engine.vote(
                page_number=page_number,
                results=agent_results
            )
            voting_results_output.append({
                "page_number": classification.page_number,
                "category": classification.category,
                "confidence": classification.confidence,
                "reasoning": classification.reasoning,
                "review_required": classification.review_required
            })

            print(f"Voting completed for page {page_number}")

            if review_task:
                self.review_manager.submit_review(review_task)

            page_classifications[page_number] = classification

        # Step 2: Boundary Detection & Conflict Checking
        # We'll determine boundaries for each page. Page 1 is always a boundary.
        boundaries: Dict[int, bool] = {1: True}

        sorted_pages = sorted(pages.keys())
        for idx in range(1, len(sorted_pages)):
            curr_page = sorted_pages[idx]
            prev_page = sorted_pages[idx - 1]

            prev_class = page_classifications[prev_page]
            curr_class = page_classifications[curr_page]

            is_boundary = False

            if prev_class.category != "Unknown" and curr_class.category != "Unknown":
                # Call Gemini boundary detector
                bd_res = self.boundary_detector.detect_boundary(
                    page_number=curr_page,
                    text=pages[curr_page],
                    prev_page_number=prev_page,
                    prev_text=pages[prev_page],
                    category=curr_class.category if prev_class.category == curr_class.category else f"{prev_class.category} -> {curr_class.category}"
                )
                bd_is_boundary = bd_res["is_boundary"]
                bd_reason = bd_res["reasoning"]

                cat_changed = prev_class.category != curr_class.category

                # Conflict checking
                if cat_changed and not bd_is_boundary:
                    # Conflict: category changed but boundary detector says same doc
                    curr_class.review_required = True
                    is_boundary = True  # Fallback: force boundary partition
                    self.review_manager.submit_review(ReviewTask(
                        page_number=curr_page,
                        reason=f"Conflict: Category changed from {prev_class.category} to {curr_class.category} but boundary detector reports no boundary.",
                        confidence=curr_class.confidence,
                        agent_votes=[],
                        winning_category=curr_class.category,
                        reasoning=bd_reason or curr_class.reasoning
                    ))
                elif not cat_changed and bd_is_boundary:
                    # Conflict: category is same but boundary detector says new doc
                    curr_class.review_required = True
                    is_boundary = True  # Follow boundary decision
                    self.review_manager.submit_review(ReviewTask(
                        page_number=curr_page,
                        reason="Conflict: Category is same but boundary detector reports boundary.",
                        confidence=curr_class.confidence,
                        agent_votes=[],
                        winning_category=curr_class.category,
                        reasoning=bd_reason or curr_class.reasoning
                    ))
                else:
                    # Agreed boundary decision
                    is_boundary = bd_is_boundary
            else:
                # Fallback if any page classification is Unknown
                is_boundary = prev_class.category != curr_class.category

            boundaries[curr_page] = is_boundary

        # Step 3: Segmentation
        segments: List[Segment] = []
        segment_id = 1
        current_pages = []
        current_category = None

        # Helper to construct and add a segment
        def add_segment(seg_id, seg_category, page_list):
            if not page_list:
                return None
            
            # Segment level confidence is the average of page confidences
            seg_conf = sum(page_classifications[p].confidence for p in page_list) / len(page_list)
            # Segment review required is True if any page requires review
            seg_review = any(page_classifications[p].review_required for p in page_list)

            segment_obj = Segment(
                segment_id=seg_id,
                category=seg_category,
                start_page=page_list[0],
                end_page=page_list[-1],
                pages=page_list
            )
            
            # Return dict matching both Pydantic Segment and extra fields for Exporter
            return {
                "obj": segment_obj,
                "extra": {
                    "segment_id": seg_id,
                    "category": seg_category,
                    "start_page": page_list[0],
                    "end_page": page_list[-1],
                    "pages": page_list,
                    "confidence": seg_conf,
                    "review_required": seg_review
                }
            }

        segment_extra_list = []
        segment_objs = []

        for page in sorted_pages:
            if boundaries.get(page, False):
                # Close existing segment
                if current_pages:
                    seg_data = add_segment(segment_id, current_category, current_pages)
                    if seg_data:
                        segment_objs.append(seg_data["obj"])
                        segment_extra_list.append(seg_data["extra"])
                        segment_id += 1
                current_pages = [page]
                current_category = page_classifications[page].category
            else:
                current_pages.append(page)

        # Close final segment
        if current_pages:
            seg_data = add_segment(segment_id, current_category, current_pages)
            if seg_data:
                segment_objs.append(seg_data["obj"])
                segment_extra_list.append(seg_data["extra"])

        # Create results dictionary
        page_results_list = [page_classifications[p] for p in sorted_pages]
        
        result_dict = {
            "document_name": os.path.basename(document_name),

            "agent_results": agent_results_output,

            "voting_results": voting_results_output,

            "review_queue": [
                review.model_dump()
                for review in self.review_manager.get_reviews()
            ],

            "page_results": [
                p.model_dump()
                for p in page_results_list
            ],

            "segments": [
                s.model_dump()
                for s in segment_objs
            ]
        }

        # Step 4: Exporting
        if self.config.get("exports", {}).get("json", True):
            json_path = f"storage/{os.path.splitext(os.path.basename(document_name))[0]}_segmented.json"
            JSONExporter.export(result_dict, json_path)
            print(f"Exported JSON results to {json_path}")

        if self.config.get("exports", {}).get("excel", True):
            excel_path = f"storage/{os.path.splitext(os.path.basename(document_name))[0]}_segmented.xlsx"
            ExcelExporter.export(segment_extra_list, excel_path)
            print(f"Exported Excel results to {excel_path}")

        print("Pipeline completed")
        return result_dict