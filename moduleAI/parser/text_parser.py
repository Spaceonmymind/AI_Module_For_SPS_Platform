# moduleAI/parser/text_parser.py

import re
from typing import Dict


class TextParser:
    """
    Разбивает текст либо по номерам, либо как одно большое эссе.
    """

    def __init__(self):
        self.section_pattern = re.compile(r'(?P<num>\d{1,2})[\.\)]?\s+(?=[А-ЯA-Z])')

    def parse(self, text: str) -> Dict[str, str]:
        matches = list(self.section_pattern.finditer(text))

        if not matches:
            # Это эссе без структуры → вернём один блок
            return {"essay": text.strip()}

        # Структурированный формат → разбиваем
        sections = {}
        for idx, match in enumerate(matches):
            section_num = match.group("num")
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            content = text[start:end].strip()
            sections[section_num] = content

        return sections
