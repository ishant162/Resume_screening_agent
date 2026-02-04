import io

import pdfplumber
import PyPDF2


class PDFExtractor:
    """Extract text from PDF resumes"""

    @staticmethod
    def extract_text_pypdf2(pdf_bytes: bytes) -> str:
        """Extract text using PyPDF2"""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            print(f"PyPDF2 extraction failed: {e}")
            return ""

    @staticmethod
    def extract_text_pdfplumber(pdf_bytes: bytes) -> str:
        """Extract text using pdfplumber (better for complex layouts)"""
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            text = ""
            with pdfplumber.open(pdf_file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text.strip()
        except Exception as e:
            print(f"pdfplumber extraction failed: {e}")
            return ""

    @classmethod
    def extract_text(cls, pdf_bytes: bytes, method: str = "pdfplumber") -> str:
        """
        Extract text from PDF bytes

        Args:
            pdf_bytes: PDF file as bytes
            method: 'pdfplumber' or 'pypdf2'

        Returns:
            Extracted text
        """
        if method == "pdfplumber":
            text = cls.extract_text_pdfplumber(pdf_bytes)
            if not text:  # Fallback to PyPDF2
                text = cls.extract_text_pypdf2(pdf_bytes)
        else:
            text = cls.extract_text_pypdf2(pdf_bytes)
            if not text:  # Fallback to pdfplumber
                text = cls.extract_text_pdfplumber(pdf_bytes)

        return text


# Quick test
if __name__ == "__main__":
    # Test with a sample PDF
    with open("data/sample_resumes/candidate_1.pdf", "rb") as f:
        pdf_bytes = f.read()

    extractor = PDFExtractor()
    text = extractor.extract_text(pdf_bytes)
    print(f"Extracted {len(text)} characters")
    print(text[:500])  # Print first 500 chars
