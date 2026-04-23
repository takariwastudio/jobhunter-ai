import io
from typing import Optional

from pypdf import PdfReader
from docx import Document
from PIL import Image
import pytesseract
import magic


class CVParser:
    SUPPORTED_MIME_TYPES = {
        "application/pdf": "pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
        "application/msword": "doc",
        "text/plain": "txt",
        "image/png": "image",
        "image/jpeg": "image",
        "image/jpg": "image",
        "image/tiff": "image",
    }

    def __init__(self):
        self._magic = magic.Magic(mime=True)

    def detect_from_bytes(self, file_bytes: bytes) -> str:
        return self._magic.from_buffer(file_bytes)

    def is_supported(self, mime_type: str) -> bool:
        return mime_type in self.SUPPORTED_MIME_TYPES

    def extract_text_from_bytes(self, file_bytes: bytes, mime_type: str) -> str:
        if not self.is_supported(mime_type):
            raise ValueError(f"Unsupported file type: {mime_type}")

        file_type = self.SUPPORTED_MIME_TYPES[mime_type]

        if file_type == "pdf":
            return self._extract_pdf(file_bytes)
        elif file_type in ("docx", "doc"):
            return self._extract_docx(file_bytes)
        elif file_type == "txt":
            return self._extract_txt(file_bytes)
        elif file_type == "image":
            return self._extract_image(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _extract_pdf(self, file_bytes: bytes) -> str:
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            parts = [page.extract_text() for page in reader.pages if page.extract_text()]
            return "\n\n".join(parts)
        except Exception as e:
            raise ValueError(f"Error reading PDF: {str(e)}")

    def _extract_docx(self, file_bytes: bytes) -> str:
        try:
            doc = Document(io.BytesIO(file_bytes))
            parts = [p.text for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(parts)
        except Exception as e:
            raise ValueError(f"Error reading DOCX: {str(e)}")

    def _extract_txt(self, file_bytes: bytes) -> str:
        for encoding in ("utf-8", "latin-1", "cp1252", "iso-8859-1"):
            try:
                return file_bytes.decode(encoding)
            except UnicodeDecodeError:
                continue
        raise ValueError("Could not decode text file with any supported encoding")

    def _extract_image(self, file_bytes: bytes) -> str:
        try:
            image = Image.open(io.BytesIO(file_bytes))
            if image.mode != "RGB":
                image = image.convert("RGB")
            return pytesseract.image_to_string(image, lang="spa+eng")
        except Exception as e:
            raise ValueError(f"Error performing OCR: {str(e)}")
