from typing import Dict


class StructureValidator:
    """
    Проверяет структуру входного текста.
    """

    def __init__(self, required_keys=None):
        self.required_keys = required_keys or ["1", "2", "3", "4", "5", "6", "7"]

    def validate(self, sections: Dict[str, str]) -> Dict:
        """
        Валидирует структуру текста: idea или essay
        :param sections: словарь после парсинга
        :return: словарь с флагами и недостающими разделами
        """
        if "essay" in sections:
            return {
                "is_essay": True,
                "valid": True,
                "missing_sections": [],
                "message": "Свободная структура эссе. Валидация не требуется."
            }

        missing = [key for key in self.required_keys if key not in sections]

        return {
            "is_essay": False,
            "valid": len(missing) == 0,
            "missing_sections": missing,
            "message": (
                "Идея содержит все обязательные разделы." if not missing
                else f"Отсутствуют разделы: {', '.join(missing)}"
            )
        }
