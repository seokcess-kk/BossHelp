"""Title-based Entity Extractor for BossHelp.

청크 제목에서 주 엔티티(primary_entity)를 추출합니다.
Wiki 페이지 제목 패턴을 분석하여 해당 페이지의 주제를 식별합니다.
"""

import re
from dataclasses import dataclass


@dataclass
class ExtractedEntity:
    """추출된 엔티티 정보."""

    name: str  # 원본 엔티티명
    normalized: str  # 정규화된 엔티티명 (lowercase, trimmed)


class TitleEntityExtractor:
    """Title에서 주 엔티티 추출.

    Wiki 제목 패턴을 분석하여 해당 페이지의 주제(primary entity)를 식별.

    Examples:
        >>> extractor = TitleEntityExtractor()
        >>> result = extractor.extract("Malenia Blade of Miquella | Elden Ring Wiki")
        >>> result.name
        'Malenia Blade of Miquella'
    """

    # Wiki 제목 패턴 (게임별)
    WIKI_PATTERNS = [
        # "Malenia Blade of Miquella | Elden Ring Wiki"
        r"^(.+?)\s*\|\s*(?:Elden Ring|Dark Souls|Sekiro|Hollow Knight|Lies of P)[^|]*Wiki",
        # "Malenia Blade of Miquella - Elden Ring Wiki Guide"
        r"^(.+?)\s*-\s*(?:Elden Ring|Dark Souls|Sekiro)[^-]*(?:Wiki|Guide)",
        # "Malenia Blade of Miquella" (단순 제목, 대문자로 시작)
        r"^([A-Z][A-Za-z\s,'-]+)$",
    ]

    # 제외 패턴 (일반 카테고리 페이지)
    EXCLUDE_PATTERNS = [
        r"^(?:All\s+)?Bosses?\b",
        r"^(?:All\s+)?Weapons?\b",
        r"^(?:All\s+)?Armou?rs?\b",
        r"^(?:All\s+)?Items?\b",
        r"^(?:Full\s+)?Walkthrough\b",
        r"^(?:Beginner'?s?\s+)?Guide\b",
        r"^(?:Game\s+)?Tips\b",
        r"^(?:All\s+)?Locations?\b",
        r"^(?:All\s+)?NPCs?\b",
        r"^Interactive\s+Map\b",
        r"^DLC\b",
        r"^Patch\s+Notes?\b",
        r"^Classes?\b",
        r"^Stats?\b",
        r"^Builds?\b",
        r"^Controls?\b",
        r"^Multiplayer\b",
        r"^Crafting\b",
        r"^New\s+Game\b",
        r"^FAQ\b",
        r"^Trophies?\b",
        r"^Achievements?\b",
    ]

    def extract(self, title: str) -> ExtractedEntity | None:
        """
        Title에서 primary entity 추출.

        Args:
            title: 청크 제목 (예: "Malenia Blade of Miquella | Elden Ring Wiki")

        Returns:
            ExtractedEntity or None if extraction failed

        Examples:
            >>> extractor = TitleEntityExtractor()
            >>> extractor.extract("Malenia Blade of Miquella | Elden Ring Wiki")
            ExtractedEntity(name='Malenia Blade of Miquella', normalized='malenia blade of miquella')

            >>> extractor.extract("All Bosses | Elden Ring Wiki")
            None  # 제외 패턴 매칭
        """
        if not title:
            return None

        title = title.strip()

        # 패턴 매칭으로 엔티티명 추출
        entity_name = None
        for pattern in self.WIKI_PATTERNS:
            match = re.match(pattern, title, re.IGNORECASE)
            if match:
                entity_name = match.group(1).strip()
                break

        if not entity_name:
            return None

        # 제외 대상 확인
        if self._should_exclude(entity_name):
            return None

        # 길이 검증 (너무 짧거나 긴 이름 제외)
        if len(entity_name) < 3 or len(entity_name) > 80:
            return None

        # 특수문자만 있는 경우 제외
        if not any(c.isalnum() for c in entity_name):
            return None

        return ExtractedEntity(
            name=entity_name,
            normalized=entity_name.lower().strip(),
        )

    def _should_exclude(self, name: str) -> bool:
        """제외 대상인지 확인."""
        for pattern in self.EXCLUDE_PATTERNS:
            if re.match(pattern, name, re.IGNORECASE):
                return True
        return False

    def extract_batch(self, titles: list[str]) -> list[ExtractedEntity | None]:
        """
        여러 제목에서 일괄 추출.

        Args:
            titles: 제목 목록

        Returns:
            ExtractedEntity 목록 (추출 실패 시 None)
        """
        return [self.extract(title) for title in titles]


# Singleton
_extractor: TitleEntityExtractor | None = None


def get_title_extractor() -> TitleEntityExtractor:
    """TitleEntityExtractor 싱글톤."""
    global _extractor
    if _extractor is None:
        _extractor = TitleEntityExtractor()
    return _extractor
