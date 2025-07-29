from docx import Document


def extract_text_from_docx(path: str) -> str:
    doc = Document(path)
    return "\n".join([p.text.strip() for p in doc.paragraphs if p.text.strip()])
