"""Unit tests for EntityTypeClassifier."""

import pytest
from app.core.entity.type_classifier import (
    EntityType,
    EntityTypeClassifier,
    get_type_classifier,
)


class TestEntityTypeClassifier:
    """EntityTypeClassifier 테스트."""

    def setup_method(self):
        """테스트 전 초기화."""
        self.classifier = EntityTypeClassifier()

    # ========================================
    # 카테고리 기반 분류 테스트
    # ========================================

    def test_classify_by_category_boss_guide(self):
        """boss_guide 카테고리 분류 테스트."""
        result = self.classifier.classify("Malenia", "boss_guide")
        assert result == EntityType.BOSS

    def test_classify_by_category_npc_quest(self):
        """npc_quest 카테고리 분류 테스트."""
        result = self.classifier.classify("Ranni", "npc_quest")
        assert result == EntityType.NPC

    def test_classify_by_category_item_location(self):
        """item_location 카테고리 분류 테스트."""
        result = self.classifier.classify("Golden Rune", "item_location")
        assert result == EntityType.ITEM

    def test_classify_by_category_progression_route(self):
        """progression_route 카테고리 분류 테스트."""
        result = self.classifier.classify("Limgrave", "progression_route")
        assert result == EntityType.LOCATION

    def test_classify_by_category_build_guide(self):
        """build_guide 카테고리 분류 테스트."""
        result = self.classifier.classify("Strength Build", "build_guide")
        assert result == EntityType.MECHANIC

    # ========================================
    # 알려진 엔티티 분류 테스트
    # ========================================

    def test_classify_known_boss_malenia(self):
        """알려진 보스 (Malenia) 분류 테스트."""
        result = self.classifier.classify("Malenia Blade of Miquella")
        assert result == EntityType.BOSS

    def test_classify_known_boss_radahn(self):
        """알려진 보스 (Radahn) 분류 테스트."""
        result = self.classifier.classify("Starscourge Radahn")
        assert result == EntityType.BOSS

    def test_classify_known_weapon_moonveil(self):
        """알려진 무기 (Moonveil) 분류 테스트."""
        result = self.classifier.classify("Moonveil")
        assert result == EntityType.WEAPON

    def test_classify_known_weapon_rivers_of_blood(self):
        """알려진 무기 (Rivers of Blood) 분류 테스트."""
        result = self.classifier.classify("Rivers of Blood")
        assert result == EntityType.WEAPON

    def test_classify_known_npc_ranni(self):
        """알려진 NPC (Ranni) 분류 테스트."""
        result = self.classifier.classify("Ranni the Witch")
        assert result == EntityType.NPC

    def test_classify_known_npc_blaidd(self):
        """알려진 NPC (Blaidd) 분류 테스트."""
        result = self.classifier.classify("Blaidd")
        assert result == EntityType.NPC

    def test_classify_known_location_limgrave(self):
        """알려진 장소 (Limgrave) 분류 테스트."""
        result = self.classifier.classify("Limgrave")
        assert result == EntityType.LOCATION

    def test_classify_known_location_leyndell(self):
        """알려진 장소 (Leyndell) 분류 테스트."""
        result = self.classifier.classify("Leyndell Royal Capital")
        assert result == EntityType.LOCATION

    # ========================================
    # 키워드 기반 분류 테스트
    # ========================================

    def test_classify_by_keyword_sword(self):
        """Sword 키워드 분류 테스트."""
        result = self.classifier.classify("Iron Straight Sword")
        assert result == EntityType.WEAPON

    def test_classify_by_keyword_katana(self):
        """Katana 키워드 분류 테스트."""
        result = self.classifier.classify("Nagakiba Katana")
        assert result == EntityType.WEAPON

    def test_classify_by_keyword_castle(self):
        """Castle 키워드 분류 테스트."""
        result = self.classifier.classify("Stormveil Castle")
        assert result == EntityType.LOCATION

    def test_classify_by_keyword_ruins(self):
        """Ruins 키워드 분류 테스트."""
        result = self.classifier.classify("Waypoint Ruins")
        assert result == EntityType.LOCATION

    def test_classify_by_keyword_armor(self):
        """Armor 키워드 분류 테스트."""
        result = self.classifier.classify("Raging Wolf Armor")
        assert result == EntityType.ARMOR

    def test_classify_by_keyword_helm(self):
        """Helm 키워드 분류 테스트."""
        result = self.classifier.classify("Bull-Goat Helm")
        assert result == EntityType.ARMOR

    def test_classify_by_keyword_talisman(self):
        """Talisman 키워드 분류 테스트."""
        result = self.classifier.classify("Crimson Amber Talisman")
        assert result == EntityType.ITEM

    def test_classify_by_keyword_incantation(self):
        """Incantation 키워드 분류 테스트."""
        result = self.classifier.classify("Flame Sling Incantation")
        assert result == EntityType.SPELL

    def test_classify_by_keyword_sorcery(self):
        """Sorcery 키워드 분류 테스트."""
        result = self.classifier.classify("Comet Azur Sorcery")
        assert result == EntityType.SPELL

    def test_classify_by_keyword_ash_of_war(self):
        """Ash of War 키워드 분류 테스트."""
        result = self.classifier.classify("Ash of War: Bloodhound's Step")
        assert result == EntityType.SPELL

    def test_classify_by_keyword_demigod(self):
        """Demigod 키워드 분류 테스트."""
        result = self.classifier.classify("Unknown Demigod")
        assert result == EntityType.BOSS

    def test_classify_by_keyword_dragon(self):
        """Dragon 키워드 분류 테스트."""
        result = self.classifier.classify("Ancient Dragon")
        assert result == EntityType.BOSS

    # ========================================
    # 우선순위 테스트
    # ========================================

    def test_priority_category_over_keywords_for_boss(self):
        """boss_guide 카테고리가 키워드보다 우선 테스트."""
        # "Castle" 키워드가 있지만 boss_guide 카테고리가 우선
        result = self.classifier.classify("Castle Guardian", "boss_guide")
        assert result == EntityType.BOSS

    def test_priority_known_entity_over_keywords(self):
        """알려진 엔티티가 키워드보다 우선 테스트."""
        # "Malenia"는 알려진 보스이므로 다른 키워드 무시
        result = self.classifier.classify("Malenia")
        assert result == EntityType.BOSS

    # ========================================
    # Unknown 분류 테스트
    # ========================================

    def test_classify_unknown_entity(self):
        """알 수 없는 엔티티 분류 테스트."""
        result = self.classifier.classify("Random Unknown Thing")
        assert result == EntityType.UNKNOWN

    def test_classify_with_category_fallback(self):
        """카테고리 폴백 분류 테스트."""
        result = self.classifier.classify("Unknown Entity", "mechanic_tip")
        assert result == EntityType.MECHANIC

    # ========================================
    # 배치 분류 테스트
    # ========================================

    def test_classify_batch(self):
        """배치 분류 테스트."""
        entities = [
            ("Malenia", "boss_guide"),
            ("Moonveil", None),
            ("Stormveil Castle", "progression_route"),
            ("Unknown", None),
        ]
        results = self.classifier.classify_batch(entities)

        assert len(results) == 4
        assert results[0] == EntityType.BOSS
        assert results[1] == EntityType.WEAPON
        assert results[2] == EntityType.LOCATION
        assert results[3] == EntityType.UNKNOWN

    # ========================================
    # 싱글톤 테스트
    # ========================================

    def test_singleton(self):
        """싱글톤 인스턴스 테스트."""
        instance1 = get_type_classifier()
        instance2 = get_type_classifier()
        assert instance1 is instance2


class TestEntityType:
    """EntityType 열거형 테스트."""

    def test_entity_type_values(self):
        """EntityType 값 테스트."""
        assert EntityType.BOSS.value == "boss"
        assert EntityType.WEAPON.value == "weapon"
        assert EntityType.ARMOR.value == "armor"
        assert EntityType.LOCATION.value == "location"
        assert EntityType.NPC.value == "npc"
        assert EntityType.ITEM.value == "item"
        assert EntityType.SPELL.value == "spell"
        assert EntityType.MECHANIC.value == "mechanic"
        assert EntityType.UNKNOWN.value == "unknown"

    def test_entity_type_count(self):
        """EntityType 개수 테스트."""
        assert len(EntityType) == 9
