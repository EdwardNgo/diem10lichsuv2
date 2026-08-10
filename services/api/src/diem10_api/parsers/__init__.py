from diem10_api.parsers.docx_reader import read_docx_paragraphs
from diem10_api.parsers.manual_exam import parse_manual_exam_lines
from diem10_api.parsers.pdf_reader import OcrNotSupportedError, read_pdf_lines
from diem10_api.parsers.types import ParsedExamDraft

DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
PDF_MIME = "application/pdf"


class UnsupportedSourceDocumentError(Exception):
    pass


def parse_source(
    content: bytes,
    mime_type: str,
    *,
    fallback_title: str = "Bản nháp import",
) -> ParsedExamDraft:
    if mime_type == DOCX_MIME:
        lines = read_docx_paragraphs(content)
    elif mime_type == PDF_MIME:
        lines = read_pdf_lines(content)
    else:
        raise UnsupportedSourceDocumentError(f"Unsupported mime type: {mime_type}")
    return parse_manual_exam_lines(lines, fallback_title=fallback_title)


__all__ = [
    "OcrNotSupportedError",
    "ParsedExamDraft",
    "UnsupportedSourceDocumentError",
    "parse_source",
]
