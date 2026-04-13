import os
import io
from typing import Optional
from pathlib import Path

from pypdf import PdfReader
from docx import Document
from PIL import Image
import pytesseract
import magic


class CVParser:
    """Service for extracting text from various CV file formats."""

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
        self.mime = magic.Magic(mime=True)

    def detect_file_type(self, file_path: str) -> str:
        """Detect MIME type of file."""
        mime_type = self.mime.from_file(file_path)
        return mime_type

    def is_supported(self, mime_type: str) -> bool:
        """Check if file type is supported."""
        return mime_type in self.SUPPORTED_MIME_TYPES

    def extract_text(self, file_path: str, mime_type: Optional[str] = None) -> str:
        """
        Extract text from a CV file.

        Args:
            file_path: Path to the file
            mime_type: Optional MIME type (will auto-detect if not provided)

        Returns:
            Extracted text as string

        Raises:
            ValueError: If file type is not supported
        """
        if mime_type is None:
            mime_type = self.detect_file_type(file_path)

        if not self.is_supported(mime_type):
            raise ValueError(f"Unsupported file type: {mime_type}")

        file_type = self.SUPPORTED_MIME_TYPES[mime_type]

        if file_type == "pdf":
            return self._extract_pdf(file_path)
        elif file_type == "docx":
            return self._extract_docx(file_path)
        elif file_type == "txt":
            return self._extract_txt(file_path)
        elif file_type == "image":
            return self._extract_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

    def _extract_pdf(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text_parts = []
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
        except Exception as e:
            raise ValueError(f"Error reading PDF: {str(e)}")

        return "\n\n".join(text_parts)

    def _extract_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        try:
            doc = Document(file_path)
            text_parts = []
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            return "\n\n".join(text_parts)
        except Exception as e:
            raise ValueError(f"Error reading DOCX: {str(e)}")

    def _extract_txt(self, file_path: str) -> str:
        """Extract text from TXT file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encodings
            for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        return f.read()
                except UnicodeDecodeError:
                    continue
            raise ValueError("Could not decode text file")
        except Exception as e:
            raise ValueError(f"Error reading TXT: {str(e)}")

    def _extract_image(self, file_path: str) -> str:
        """Extract text from image using OCR."""
        try:
            image = Image.open(file_path)
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            text = pytesseract.image_to_string(image, lang='spa+eng')
            return text
        except Exception as e:
            raise ValueError(f"Error performing OCR: {str(e)}")

    def extract_metadata(self, file_path: str) -> dict:
        """Extract metadata from file."""
        stat = os.stat(file_path)
        mime_type = self.detect_file_type(file_path)

        return {
            "file_size": stat.st_size,
            "mime_type": mime_type,
            "file_type": self.SUPPORTED_MIME_TYPES.get(mime_type, "unknown"),
            "file_name": Path(file_path).name,
        }
