import re
import unicodedata


def normalize_line(line: str) -> str:
    text = unicodedata.normalize("NFC", line)
    text = text.replace("\u00ad", "")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    return re.sub(r"\s+", " ", text).strip()


def normalize_lines(lines: list[str]) -> list[str]:
    return [normalized for line in lines if (normalized := normalize_line(line))]
