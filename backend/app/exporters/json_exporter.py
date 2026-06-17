import json
import os
from typing import Dict, Any


class JSONExporter:

    @staticmethod
    def export(data: Dict[str, Any], filepath: str) -> str:
        """
        Exports the pipeline result dictionary to a JSON file.
        """
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)
        return filepath
