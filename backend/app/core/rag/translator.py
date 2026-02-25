"""Query Translator with Haiku + Caching.

한글 질문을 영어로 번역하여 영어 데이터베이스와 매칭되도록 합니다.
Haiku 모델을 사용하여 빠르고 저렴한 번역을 제공합니다.
"""

import hashlib
import logging
from anthropic import Anthropic

from app.config import get_settings

logger = logging.getLogger(__name__)


class QueryTranslator:
    """한글 질문을 영어로 번역 (Haiku + 캐싱)."""

    def __init__(self):
        settings = get_settings()
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self._cache: dict[str, str] = {}  # 세션 내 캐시

    def translate(self, question: str, game_id: str) -> str:
        """
        한글 질문을 영어로 번역. 캐시 우선 확인.

        Args:
            question: 사용자 질문 (한글 또는 영어)
            game_id: 게임 ID (예: 'elden-ring', 'dark-souls-3')

        Returns:
            영어로 번역된 질문 (이미 영어면 그대로 반환)
        """
        # 이미 영어면 그대로 반환
        if not self._contains_korean(question):
            logger.debug(f"Question already in English: {question[:50]}...")
            return question

        # 캐시 확인
        cache_key = self._make_cache_key(question, game_id)
        if cache_key in self._cache:
            logger.debug(f"Cache hit for question: {question[:30]}...")
            return self._cache[cache_key]

        # Haiku로 번역
        translated = self._translate_with_haiku(question, game_id)

        # 캐시 저장
        self._cache[cache_key] = translated
        logger.info(f"Translated: '{question[:30]}...' -> '{translated[:50]}...'")

        return translated

    def _translate_with_haiku(self, question: str, game_id: str) -> str:
        """Claude Haiku로 번역 (빠르고 저렴)."""
        # 게임 이름 포맷팅 (dark-souls-3 -> Dark Souls 3)
        game_name = game_id.replace("-", " ").title()

        prompt = f"""Translate this gaming question to English.
Game: {game_name}
Question: {question}

Rules:
- Keep game-specific terms (boss names, item names, location names) in their original English form
- Translate the question naturally for a game guide search
- Output ONLY the translated question, nothing else"""

        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            # 폴백: 엔티티 사전으로 한글 → 영어 치환
            return self._fallback_with_dictionary(question, game_id)

    def _fallback_with_dictionary(self, question: str, game_id: str) -> str:
        """엔티티 사전 기반 폴백 번역.

        Haiku 번역 실패 시 엔티티 사전을 사용하여
        알려진 게임 용어만이라도 영어로 변환.

        Args:
            question: 원본 한글 질문
            game_id: 게임 ID

        Returns:
            부분 번역된 질문 (엔티티만 영어로 변환)
        """
        try:
            from app.core.entity.dictionary import get_entity_dictionary
            entity_dict = get_entity_dictionary(game_id, auto_expand=False)
            translated = entity_dict.translate_to_english(question)
            if translated != question:
                logger.info(f"Fallback translation applied: '{question[:30]}' -> '{translated[:50]}'")
            return translated
        except Exception as e:
            logger.error(f"Fallback translation also failed: {e}")
            return question

    def _contains_korean(self, text: str) -> bool:
        """텍스트에 한글이 포함되어 있는지 확인."""
        return any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in text)

    def _make_cache_key(self, question: str, game_id: str) -> str:
        """캐시 키 생성."""
        content = f"{game_id}:{question}"
        return hashlib.md5(content.encode()).hexdigest()


# Singleton
_translator: QueryTranslator | None = None


def get_query_translator() -> QueryTranslator:
    """QueryTranslator 싱글톤 인스턴스 반환."""
    global _translator
    if _translator is None:
        _translator = QueryTranslator()
    return _translator
