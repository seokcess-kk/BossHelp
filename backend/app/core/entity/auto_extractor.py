"""Entity Auto Extractor for BossHelp.

크롤링된 청크 제목에서 엔티티를 자동 추출하여 사전 확장.
"""

import re
from functools import lru_cache
from supabase import Client
from app.db.supabase import get_supabase_client


class EntityAutoExtractor:
    """청크 제목에서 엔티티 자동 추출."""

    # Wiki 제목 패턴
    WIKI_TITLE_PATTERNS = [
        # "Malenia Blade of Miquella | Elden Ring Wiki"
        r"^(.+?)\s*\|\s*(?:Elden Ring|Dark Souls|Sekiro|Hollow Knight|Lies of P)[^|]*Wiki",
        # "Malenia Blade of Miquella"
        r"^([A-Z][^|]+)$",
    ]

    # 제외 패턴 (일반 페이지)
    EXCLUDE_PATTERNS = [
        r"^Builds?\b",
        r"^Weapons?\b",
        r"^Armor\b",
        r"^Items?\b",
        r"^Walkthrough\b",
        r"^Guide\b",
        r"^Tips\b",
        r"^Locations?\b",
        r"^NPCs?\b",
        r"^Bosses\b",
        r"^Enemies\b",
        r"^Maps?\b",
        r"^Interactive\b",
    ]

    def __init__(self, client: Client | None = None):
        self.client = client or get_supabase_client()
        self._cache: dict[str, dict[str, str]] = {}

    def extract_from_game(self, game_id: str) -> dict[str, str]:
        """게임의 모든 청크에서 엔티티 추출.

        Args:
            game_id: 게임 ID (e.g., 'elden-ring')

        Returns:
            엔티티 사전 {lowercase_name: original_name}
        """
        # 캐시 확인
        if game_id in self._cache:
            return self._cache[game_id]

        # 고유 제목 조회
        result = self.client.table("chunks").select(
            "title"
        ).eq("game_id", game_id).eq("is_active", True).execute()

        if not result.data:
            return {}

        # 제목에서 엔티티 추출
        entities: dict[str, str] = {}
        seen_titles: set[str] = set()

        for chunk in result.data:
            title = chunk.get("title", "")
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)

            # 패턴 매칭으로 엔티티명 추출
            entity_name = self._extract_entity_name(title)
            if entity_name and not self._should_exclude(entity_name):
                # 정규화된 키 생성 (소문자, 앞뒤 공백 제거)
                key = entity_name.lower().strip()
                if key not in entities and len(key) >= 3:
                    entities[key] = entity_name

        # 캐시 저장
        self._cache[game_id] = entities
        return entities

    def _extract_entity_name(self, title: str) -> str | None:
        """제목에서 엔티티명 추출."""
        title = title.strip()

        for pattern in self.WIKI_TITLE_PATTERNS:
            match = re.match(pattern, title, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # 너무 짧거나 긴 이름 제외
                if 3 <= len(name) <= 100:
                    return name
        return None

    def _should_exclude(self, name: str) -> bool:
        """제외 대상인지 확인."""
        for pattern in self.EXCLUDE_PATTERNS:
            if re.match(pattern, name, re.IGNORECASE):
                return True
        return False

    def merge_with_manual_dict(
        self,
        auto_entities: dict[str, str],
        manual_dict: dict[str, str]
    ) -> dict[str, str]:
        """자동 추출 엔티티와 수동 사전 병합.

        수동 사전이 우선순위를 가짐 (한글 → 영어 매핑 유지).

        Args:
            auto_entities: 자동 추출된 엔티티 {key: name}
            manual_dict: 수동 관리 사전 {korean: english}

        Returns:
            병합된 사전
        """
        merged = dict(manual_dict)  # 수동 사전 복사

        # 수동 사전의 영어 값들 (중복 체크용)
        manual_values_lower = {v.lower() for v in manual_dict.values()}

        # 자동 추출된 엔티티 중 수동 사전에 없는 것만 추가
        for key, value in auto_entities.items():
            if value.lower() not in manual_values_lower:
                # 영어 엔티티는 그대로 추가 (영어 → 영어)
                merged[value] = value

        return merged

    def clear_cache(self, game_id: str | None = None):
        """캐시 클리어.

        Args:
            game_id: 특정 게임만 클리어. None이면 전체 클리어.
        """
        if game_id:
            self._cache.pop(game_id, None)
        else:
            self._cache.clear()


# Singleton
_extractor: EntityAutoExtractor | None = None


def get_entity_extractor() -> EntityAutoExtractor:
    """EntityAutoExtractor 싱글톤."""
    global _extractor
    if _extractor is None:
        _extractor = EntityAutoExtractor()
    return _extractor
