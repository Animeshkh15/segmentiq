import pandas as pd
import os
from typing import List, Dict, Any


class ExcelExporter:

    @staticmethod
    def export(segments: List[Dict[str, Any]], filepath: str) -> str:
        """
        Exports the segments list to an Excel spreadsheet.
        Columns:
        - Segment ID
        - Category
        - Start Page
        - End Page
        - Total Pages
        - Confidence
        - Review Required
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        rows = []
        for segment in segments:
            pages = segment.get("pages", [])
            total_pages = len(pages)
            rows.append({
                "Segment ID": segment.get("segment_id"),
                "Category": segment.get("category"),
                "Start Page": segment.get("start_page"),
                "End Page": segment.get("end_page"),
                "Total Pages": total_pages,
                "Confidence": round(segment.get("confidence", 0.0), 2),
                "Review Required": "Yes" if segment.get("review_required", False) else "No"
            })

        df = pd.DataFrame(rows)
        df.to_excel(filepath, index=False)
        return filepath
