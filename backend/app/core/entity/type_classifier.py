"""Entity Type Classifier for BossHelp.

엔티티를 유형별로 분류합니다 (boss, weapon, location 등).
카테고리, 키워드, 알려진 엔티티 사전을 기반으로 분류합니다.
"""

from enum import Enum


class EntityType(str, Enum):
    """엔티티 유형."""

    BOSS = "boss"
    WEAPON = "weapon"
    ARMOR = "armor"
    LOCATION = "location"
    NPC = "npc"
    ITEM = "item"
    SPELL = "spell"
    MECHANIC = "mechanic"
    UNKNOWN = "unknown"


class EntityTypeClassifier:
    """엔티티 유형 분류기.

    category + entity_name + keyword 기반으로 엔티티 유형 결정.

    분류 우선순위:
    1. 카테고리 기반 (boss_guide → boss)
    2. 알려진 엔티티 사전 (Malenia → boss)
    3. 키워드 기반 (Sword → weapon)
    """

    # 카테고리 → 기본 유형 매핑
    CATEGORY_MAPPING = {
        "boss_guide": EntityType.BOSS,
        "item_location": EntityType.ITEM,
        "build_guide": EntityType.MECHANIC,
        "mechanic_tip": EntityType.MECHANIC,
        "npc_quest": EntityType.NPC,
        "progression_route": EntityType.LOCATION,
        "secret_hidden": EntityType.LOCATION,
    }

    # 키워드 기반 유형 분류
    TYPE_KEYWORDS: dict[EntityType, list[str]] = {
        EntityType.BOSS: [
            "Demigod",
            "Lord",
            "King",
            "Queen",
            "Knight",
            "Dragon",
            "Omen",
            "Beast",
            "God",
            "Godfrey",
            "Radagon",
            "Maliketh",
            "Grafted",
            "Champion",
            "Apostle",
            "Sentinel",
            "Giant",
            "Avatar",
            "Crucible",
            "Ulcerated",
            "Erdtree",
            "Godskin",
            "Valiant",
            "Cleanrot",
            "Commander",
            "Abductor",
            "Wormface",
        ],
        EntityType.WEAPON: [
            "Sword",
            "Katana",
            "Blade",
            "Staff",
            "Seal",
            "Shield",
            "Bow",
            "Crossbow",
            "Spear",
            "Halberd",
            "Axe",
            "Hammer",
            "Dagger",
            "Claw",
            "Fist",
            "Whip",
            "Scythe",
            "Flail",
            "Greatsword",
            "Colossal",
            "Twinblade",
            "Rapier",
            "Torch",
            "Ballista",
        ],
        EntityType.ARMOR: [
            "Armor",
            "Helm",
            "Helmet",
            "Gauntlets",
            "Greaves",
            "Set",
            "Robe",
            "Cloak",
            "Mask",
            "Hood",
            "Crown",
            "Altered",
        ],
        EntityType.LOCATION: [
            "Castle",
            "Ruins",
            "Dungeon",
            "Cave",
            "Catacombs",
            "Tower",
            "Palace",
            "Temple",
            "Shrine",
            "Gate",
            "Valley",
            "Lake",
            "Mountain",
            "Plateau",
            "Grave",
            "Tunnel",
            "Shack",
            "Church",
            "Evergaol",
            "Waypoint",
            "Capital",
            "Academy",
            "Manor",
        ],
        EntityType.NPC: [
            "Merchant",
            "Maiden",
            "Finger",
            "Tarnished",
            "Witch",
            "Sorcerer",
            "Prophet",
            "Warrior",
            "Samurai",
            "Confessor",
            "Astrologer",
            "Prisoner",
            "Bandit",
            "Vagabond",
        ],
        EntityType.ITEM: [
            "Talisman",
            "Ring",
            "Amulet",
            "Key",
            "Bell",
            "Rune",
            "Stone",
            "Flask",
            "Tear",
            "Crystal",
            "Medallion",
            "Stonesword",
            "Needle",
            "Prayerbook",
            "Cookbook",
            "Whetblade",
            "Bell Bearing",
        ],
        EntityType.SPELL: [
            "Incantation",
            "Sorcery",
            "Spell",
            "Ash of War",
            "Skill",
            "Art",
            "Prayer",
            "Glintstone",
            "Carian",
        ],
    }

    # 알려진 엔티티 사전 (엔티티명 → 유형)
    KNOWN_ENTITIES: dict[str, EntityType] = {
        # 주요 보스 (Elden Ring)
        "malenia": EntityType.BOSS,
        "radahn": EntityType.BOSS,
        "morgott": EntityType.BOSS,
        "mohg": EntityType.BOSS,
        "rykard": EntityType.BOSS,
        "godrick": EntityType.BOSS,
        "rennala": EntityType.BOSS,
        "radagon": EntityType.BOSS,
        "maliketh": EntityType.BOSS,
        "placidusax": EntityType.BOSS,
        "godfrey": EntityType.BOSS,
        "hoarah loux": EntityType.BOSS,
        "elden beast": EntityType.BOSS,
        "margit": EntityType.BOSS,
        "fortissax": EntityType.BOSS,
        "lansseax": EntityType.BOSS,
        "fire giant": EntityType.BOSS,
        "astel": EntityType.BOSS,
        "ancestor spirit": EntityType.BOSS,
        "loretta": EntityType.BOSS,
        "renalla": EntityType.BOSS,
        # 주요 무기 (Elden Ring)
        "moonveil": EntityType.WEAPON,
        "rivers of blood": EntityType.WEAPON,
        "blasphemous blade": EntityType.WEAPON,
        "dark moon greatsword": EntityType.WEAPON,
        "starscourge greatsword": EntityType.WEAPON,
        "sword of night and flame": EntityType.WEAPON,
        "wing of astel": EntityType.WEAPON,
        "hand of malenia": EntityType.WEAPON,
        "nagakiba": EntityType.WEAPON,
        "uchigatana": EntityType.WEAPON,
        "reduvia": EntityType.WEAPON,
        "bolt of gransax": EntityType.WEAPON,
        "fallingstar beast jaw": EntityType.WEAPON,
        "mimic tear": EntityType.ITEM,  # 재료
        # 주요 NPC (Elden Ring)
        "ranni": EntityType.NPC,
        "melina": EntityType.NPC,
        "alexander": EntityType.NPC,
        "patches": EntityType.NPC,
        "blaidd": EntityType.NPC,
        "fia": EntityType.NPC,
        "goldmask": EntityType.NPC,
        "nepheli": EntityType.NPC,
        "kenneth": EntityType.NPC,
        "hyetta": EntityType.NPC,
        "millicent": EntityType.NPC,
        "seluvis": EntityType.NPC,
        "rogier": EntityType.NPC,
        "varre": EntityType.NPC,
        "hewg": EntityType.NPC,
        "roderika": EntityType.NPC,
        "gideon": EntityType.NPC,
        "thops": EntityType.NPC,
        "sellen": EntityType.NPC,
        "dung eater": EntityType.NPC,
        "corhyn": EntityType.NPC,
        # 주요 장소 (Elden Ring)
        "limgrave": EntityType.LOCATION,
        "liurnia": EntityType.LOCATION,
        "caelid": EntityType.LOCATION,
        "altus plateau": EntityType.LOCATION,
        "leyndell": EntityType.LOCATION,
        "mountaintops": EntityType.LOCATION,
        "haligtree": EntityType.LOCATION,
        "siofra river": EntityType.LOCATION,
        "ainsel river": EntityType.LOCATION,
        "nokron": EntityType.LOCATION,
        "deeproot depths": EntityType.LOCATION,
        "mohgwyn palace": EntityType.LOCATION,
        "farum azula": EntityType.LOCATION,
        "redmane castle": EntityType.LOCATION,
        "volcano manor": EntityType.LOCATION,
        "raya lucaria": EntityType.LOCATION,
        "stormveil": EntityType.LOCATION,
    }

    def classify(
        self,
        entity_name: str,
        category: str | None = None,
    ) -> EntityType:
        """
        엔티티 유형 분류.

        Args:
            entity_name: 엔티티명
            category: 청크 카테고리 (옵션)

        Returns:
            EntityType

        Examples:
            >>> classifier = EntityTypeClassifier()
            >>> classifier.classify("Malenia Blade of Miquella", "boss_guide")
            EntityType.BOSS

            >>> classifier.classify("Moonveil")
            EntityType.WEAPON  # 알려진 무기

            >>> classifier.classify("Redmane Castle", "progression_route")
            EntityType.LOCATION
        """
        # 1. 카테고리 기반 우선 분류
        if category and category in self.CATEGORY_MAPPING:
            category_type = self.CATEGORY_MAPPING[category]
            # boss_guide, npc_quest는 카테고리 신뢰
            if category in ("boss_guide", "npc_quest"):
                return category_type

        # 2. 알려진 엔티티 사전
        known_type = self._get_known_entity_type(entity_name)
        if known_type:
            return known_type

        # 3. 키워드 기반 분류
        keyword_type = self._classify_by_keywords(entity_name)
        if keyword_type:
            return keyword_type

        # 4. 카테고리 폴백
        if category and category in self.CATEGORY_MAPPING:
            return self.CATEGORY_MAPPING[category]

        return EntityType.UNKNOWN

    def _get_known_entity_type(self, entity_name: str) -> EntityType | None:
        """알려진 엔티티 유형 조회 (사전 기반)."""
        name_lower = entity_name.lower()

        # 정확히 일치
        if name_lower in self.KNOWN_ENTITIES:
            return self.KNOWN_ENTITIES[name_lower]

        # 부분 일치 (엔티티명이 포함된 경우)
        for known_name, entity_type in self.KNOWN_ENTITIES.items():
            if known_name in name_lower or name_lower in known_name:
                return entity_type

        return None

    def _classify_by_keywords(self, entity_name: str) -> EntityType | None:
        """키워드 기반 분류."""
        # 각 단어별로 키워드 매칭
        words = entity_name.split()

        for entity_type, keywords in self.TYPE_KEYWORDS.items():
            for keyword in keywords:
                # 단어 단위로 매칭 (부분 문자열 방지)
                if keyword in words:
                    return entity_type
                # 복합어 매칭 (예: "Ash of War")
                if keyword.lower() in entity_name.lower():
                    return entity_type

        return None

    def classify_batch(
        self,
        entities: list[tuple[str, str | None]],
    ) -> list[EntityType]:
        """
        여러 엔티티 일괄 분류.

        Args:
            entities: (entity_name, category) 튜플 목록

        Returns:
            EntityType 목록
        """
        return [
            self.classify(entity_name, category)
            for entity_name, category in entities
        ]


# Singleton
_classifier: EntityTypeClassifier | None = None


def get_type_classifier() -> EntityTypeClassifier:
    """EntityTypeClassifier 싱글톤."""
    global _classifier
    if _classifier is None:
        _classifier = EntityTypeClassifier()
    return _classifier
