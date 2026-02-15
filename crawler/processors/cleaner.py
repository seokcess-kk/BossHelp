"""Text Cleaner for BossHelp Data Pipeline.

HTML 제거, 정규화, 불필요한 패턴 제거 등을 수행합니다.
"""

import re
from html import unescape

import html2text
from unidecode import unidecode

from crawler.models import RawDocument, CleanedDocument


class TextCleaner:
    """텍스트 클리닝 프로세서."""

    # 제거할 패턴들
    REMOVE_PATTERNS = [
        # Reddit 관련
        r"\[deleted\]",
        r"\[removed\]",
        r"edit\s*\d*\s*:",
        r"^TL;?DR:?",
        r"^EDIT\s*\d*\s*:",

        # 링크/이미지
        r"!\[.*?\]\(.*?\)",  # Markdown 이미지
        r"\[(.+?)\]\(http[s]?://[^\)]+\)",  # Markdown 링크 (텍스트 유지)

        # 소셜 미디어
        r"follow me on \w+",
        r"subscribe to my",
        r"join my discord",
        r"check out my youtube",

        # 불필요한 메타
        r"^>.*$",  # Quote 라인 (일부만)
        r"^\*{3,}$",  # 구분선
        r"^-{3,}$",
        r"^_{3,}$",
    ]

    # 정규화할 패턴들
    NORMALIZE_PATTERNS = [
        # 연속 공백
        (r"\s+", " "),
        # 연속 줄바꿈
        (r"\n{3,}", "\n\n"),
        # 특수 유니코드
        (r"[\u200b-\u200f\u2028-\u202f]", ""),
    ]

    def __init__(self):
        self.html2text = html2text.HTML2Text()
        self.html2text.ignore_links = False
        self.html2text.ignore_images = True
        self.html2text.body_width = 0

    def clean(self, doc: RawDocument) -> CleanedDocument:
        """
        문서 클리닝.

        1. HTML → 텍스트 변환
        2. 불필요한 패턴 제거
        3. 텍스트 정규화
        4. 길이 검증
        """
        content = doc.content
        original_length = len(content)

        # HTML 엔티티 디코딩
        content = unescape(content)

        # HTML 태그가 포함된 경우 변환
        if "<" in content and ">" in content:
            content = self.html2text.handle(content)

        # 불필요한 패턴 제거
        for pattern in self.REMOVE_PATTERNS:
            content = re.sub(pattern, "", content, flags=re.MULTILINE | re.IGNORECASE)

        # Markdown 링크에서 텍스트만 추출
        content = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", content)

        # 정규화
        for pattern, replacement in self.NORMALIZE_PATTERNS:
            content = re.sub(pattern, replacement, content)

        # 앞뒤 공백 정리
        content = content.strip()

        # 제목 정리
        title = doc.title.strip()
        title = re.sub(r"\s+", " ", title)

        return CleanedDocument(
            game_id=doc.game_id,
            source_type=doc.source_type,
            source_url=doc.source_url,
            title=title,
            content=content,
            original_length=original_length,
            cleaned_length=len(content),
            upvotes=doc.upvotes,
            created_at=doc.created_at,
            flair=doc.flair,
        )

    def clean_batch(self, docs: list[RawDocument]) -> list[CleanedDocument]:
        """배치 클리닝."""
        cleaned = []
        for doc in docs:
            try:
                cleaned_doc = self.clean(doc)
                # 너무 짧은 문서 필터링
                if cleaned_doc.cleaned_length >= 100:
                    cleaned.append(cleaned_doc)
            except Exception:
                continue
        return cleaned

    @staticmethod
    def normalize_entity_name(name: str) -> str:
        """엔티티 이름 정규화 (검색용)."""
        # 소문자 변환
        name = name.lower()
        # 특수문자 제거
        name = re.sub(r"[^\w\s]", "", name)
        # 공백 정규화
        name = re.sub(r"\s+", " ", name)
        return name.strip()
