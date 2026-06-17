from pdf2image import convert_from_path
import pytesseract

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Users\INT022\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
)


class OCRService:

    def extract_text(
        self,
        pdf_path: str
    ):

        images = convert_from_path(
            pdf_path,
            poppler_path=r"C:\poppler\Library\bin"
        )

        pages = {}

        for index, image in enumerate(images):

            text = pytesseract.image_to_string(
                image
            )

            pages[index + 1] = text

        return pages

    @staticmethod
    def assess_quality(text: str) -> tuple[bool, str]:
        cleaned = text.strip()
        if not cleaned:
            return True, "OCR extracted empty text"

        if len(cleaned) < 15:
            return True, f"OCR text length ({len(cleaned)}) is too short"

        alnum_count = sum(1 for c in cleaned if c.isalnum() or c.isspace())
        ratio = alnum_count / len(cleaned)
        if ratio < 0.5:
            return True, f"OCR text contains too much noise (alphanumeric ratio: {ratio:.2%})"

        return False, ""