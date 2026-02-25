"""Unit tests for TitleEntityExtractor."""

import pytest
from app.core.entity.title_extractor import (
    TitleEntityExtractor,
    ExtractedEntity,
    get_title_extractor,
)


class TestTitleEntityExtractor:
    """TitleEntityExtractor 테스트."""

    def setup_method(self):
        """테스트 전 초기화."""
        self.extractor = TitleEntityExtractor()

    # ========================================
    # 정상 추출 테스트
    # ========================================

    def test_extract_wiki_title_with_pipe(self):
        """Wiki 제목 (파이프 구분자) 추출 테스트."""
        result = self.extractor.extract("Malenia Blade of Miquella | Elden Ring Wiki")
        assert result is not None
        assert result.name == "Malenia Blade of Miquella"
        assert result.normalized == "malenia blade of miquella"

    def test_extract_wiki_title_with_dash(self):
        """Wiki 제목 (대시 구분자) 추출 테스트."""
        result = self.extractor.extract("Rivers of Blood - Elden Ring Wiki Guide")
        assert result is not None
        assert result.name == "Rivers of Blood"
        assert result.normalized == "rivers of blood"

    def test_extract_simple_title(self):
        """단순 제목 추출 테스트."""
        result = self.extractor.extract("Moonveil")
        assert result is not None
        assert result.name == "Moonveil"

    def test_extract_boss_name(self):
        """보스 이름 추출 테스트."""
        result = self.extractor.extract("Starscourge Radahn | Elden Ring Wiki")
        assert result is not None
        assert result.name == "Starscourge Radahn"

    def test_extract_location_name(self):
        """장소 이름 추출 테스트."""
        result = self.extractor.extract("Redmane Castle | Elden Ring Wiki")
        assert result is not None
        assert result.name == "Redmane Castle"

    def test_extract_npc_name(self):
        """NPC 이름 추출 테스트."""
        result = self.extractor.extract("Ranni the Witch | Elden Ring Wiki")
        assert result is not None
        assert result.name == "Ranni the Witch"

    def test_extract_different_games(self):
        """다른 게임 Wiki 제목 추출 테스트."""
        # Dark Souls
        result = self.extractor.extract("Artorias | Dark Souls Wiki")
        assert result is not None
        assert result.name == "Artorias"

        # Sekiro
        result = self.extractor.extract("Genichiro | Sekiro Wiki")
        assert result is not None
        assert result.name == "Genichiro"

        # Hollow Knight
        result = self.extractor.extract("Hornet | Hollow Knight Wiki")
        assert result is not None
        assert result.name == "Hornet"

    # ========================================
    # 제외 패턴 테스트
    # ========================================

    def test_exclude_bosses_page(self):
        """Bosses 페이지 제외 테스트."""
        result = self.extractor.extract("All Bosses | Elden Ring Wiki")
        assert result is None

    def test_exclude_weapons_page(self):
        """Weapons 페이지 제외 테스트."""
        result = self.extractor.extract("Weapons | Elden Ring Wiki")
        assert result is None

    def test_exclude_walkthrough_page(self):
        """Walkthrough 페이지 제외 테스트."""
        result = self.extractor.extract("Walkthrough | Elden Ring Wiki")
        assert result is None

    def test_exclude_builds_page(self):
        """Builds 페이지 제외 테스트."""
        result = self.extractor.extract("Builds | Elden Ring Wiki")
        assert result is None

    def test_exclude_guide_page(self):
        """Guide 페이지 제외 테스트."""
        result = self.extractor.extract("Beginner's Guide | Elden Ring Wiki")
        assert result is None

    def test_exclude_locations_page(self):
        """Locations 페이지 제외 테스트."""
        result = self.extractor.extract("All Locations | Elden Ring Wiki")
        assert result is None

    def test_exclude_interactive_map(self):
        """Interactive Map 페이지 제외 테스트."""
        result = self.extractor.extract("Interactive Map | Elden Ring Wiki")
        assert result is None

    def test_exclude_dlc_page(self):
        """DLC 페이지 제외 테스트."""
        result = self.extractor.extract("DLC | Elden Ring Wiki")
        assert result is None

    def test_exclude_patch_notes(self):
        """Patch Notes 페이지 제외 테스트."""
        result = self.extractor.extract("Patch Notes | Elden Ring Wiki")
        assert result is None

    # ========================================
    # 엣지 케이스 테스트
    # ========================================

    def test_empty_title(self):
        """빈 제목 처리 테스트."""
        result = self.extractor.extract("")
        assert result is None

    def test_none_title(self):
        """None 제목 처리 테스트."""
        result = self.extractor.extract(None)
        assert result is None

    def test_whitespace_title(self):
        """공백만 있는 제목 처리 테스트."""
        result = self.extractor.extract("   ")
        assert result is None

    def test_short_title(self):
        """너무 짧은 제목 제외 테스트."""
        result = self.extractor.extract("AB")
        assert result is None

    def test_special_characters_only(self):
        """특수문자만 있는 제목 제외 테스트."""
        result = self.extractor.extract("!@#$%")
        assert result is None

    def test_title_with_special_chars(self):
        """특수문자 포함 제목 처리 테스트."""
        result = self.extractor.extract("Sword of Night and Flame | Elden Ring Wiki")
        assert result is not None
        assert result.name == "Sword of Night and Flame"

    # ========================================
    # 배치 처리 테스트
    # ========================================

    def test_extract_batch(self):
        """배치 추출 테스트."""
        titles = [
            "Malenia Blade of Miquella | Elden Ring Wiki",
            "All Bosses | Elden Ring Wiki",
            "Moonveil | Elden Ring Wiki",
            "",
        ]
        results = self.extractor.extract_batch(titles)

        assert len(results) == 4
        assert results[0] is not None
        assert results[0].name == "Malenia Blade of Miquella"
        assert results[1] is None  # 제외됨
        assert results[2] is not None
        assert results[2].name == "Moonveil"
        assert results[3] is None  # 빈 제목

    # ========================================
    # 싱글톤 테스트
    # ========================================

    def test_singleton(self):
        """싱글톤 인스턴스 테스트."""
        instance1 = get_title_extractor()
        instance2 = get_title_extractor()
        assert instance1 is instance2


class TestExtractedEntity:
    """ExtractedEntity 데이터클래스 테스트."""

    def test_extracted_entity_creation(self):
        """ExtractedEntity 생성 테스트."""
        entity = ExtractedEntity(
            name="Malenia Blade of Miquella",
            normalized="malenia blade of miquella",
        )
        assert entity.name == "Malenia Blade of Miquella"
        assert entity.normalized == "malenia blade of miquella"
