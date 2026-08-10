import io

from pypdf import PdfReader

from diem10_api.parsers.text_lines import normalize_lines


class OcrNotSupportedError(Exception):
    pass


def read_pdf_lines(content: bytes) -> list[str]:
    reader = PdfReader(io.BytesIO(content))
    if len(reader.pages) == 0:
        raise OcrNotSupportedError("PDF has no pages")
    extracted: list[str] = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        extracted.extend(page_text.splitlines())
    lines = normalize_lines(extracted)
    if not lines:
        raise OcrNotSupportedError("PDF has no extractable text layer")
    joined = " ".join(lines)
    if len(joined.strip()) < max(40, len(reader.pages) * 8):
        raise OcrNotSupportedError("PDF appears to be scan-only or image-only")
    return lines
