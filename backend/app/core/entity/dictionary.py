"""Korean-English Entity Dictionary for BossHelp."""

import re
from functools import lru_cache


# Entity dictionaries for each game
ENTITY_DICTS: dict[str, dict[str, str]] = {
    "elden-ring": {
        # Bosses
        "말레니아": "Malenia",
        "라다곤": "Radagon",
        "마르기트": "Margit",
        "고드릭": "Godrick",
        "라단": "Radahn",
        "모르곳": "Morgott",
        "모르고트": "Morgott",
        "모그": "Mohg",
        "릭카르드": "Rykard",
        "라니": "Ranni",
        "멜리나": "Melina",
        "미켈라": "Miquella",
        "엘든 비스트": "Elden Beast",
        "화신": "Avatar",
        "플라시덕스": "Placidusax",
        "마리케스": "Maliketh",
        "호라 루": "Hoarah Loux",
        "겔미르": "Gelmir",
        "레날라": "Rennala",
        # Items
        "미믹의 눈물": "Mimic Tear",
        "출혈": "Bleed",
        "감염의 눈물": "Shard of Alexander",
        "강타의 물든 피": "Rivers of Blood",
        "서리": "Frost",
        "신성": "Sacred",
        "물리": "Physical",
        "마법": "Magic",
        "성수": "Holy Water",
        "황금 룬": "Golden Rune",
        "대룬": "Great Rune",
        # Locations
        "림그레이브": "Limgrave",
        "리에니에": "Liurnia",
        "케일리드": "Caelid",
        "알투스 고원": "Altus Plateau",
        "왕도 레인델": "Leyndell",
        "설원": "Mountaintops",
        "미켈라의 성수나무": "Haligtree",
        # Mechanics
        "회피": "Dodge",
        "가드 카운터": "Guard Counter",
        "점프 공격": "Jump Attack",
        "패링": "Parry",
        "빌드": "Build",
        "스탯": "Stats",
        "스케일링": "Scaling",
    },
    "sekiro": {
        # Bosses
        "겐이치로": "Genichiro",
        "이신": "Isshin",
        "검성": "Sword Saint",
        "에마": "Emma",
        "부엉이": "Owl",
        "시노비 사냥꾼": "Shinobi Hunter",
        "오니와": "Gyoubu",
        "나비부인": "Lady Butterfly",
        "원숭이": "Guardian Ape",
        "수정 참수형": "Corrupted Monk",
        "사자원숭이": "Lion Ape",
        "칠면무사": "Shichimen Warrior",
        "요괴": "Demon",
        # Mechanics
        "튕겨내기": "Deflect",
        "패리": "Parry",
        "미키리": "Mikiri Counter",
        "번개 반사": "Lightning Reversal",
        "체간": "Posture",
        "인술": "Prosthetic",
        "신의 달": "Divine Confetti",
    },
    "hollow-knight": {
        # Bosses
        "호넷": "Hornet",
        "그림": "Grimm",
        "몽환의 전사": "Nightmare King",
        "레이디언스": "Radiance",
        "압솔루트 레이디언스": "Absolute Radiance",
        "순수한 그릇": "Pure Vessel",
        "빈 기사": "Hollow Knight",
        "그레이 프린스": "Grey Prince Zote",
        "가디언": "Watcher Knights",
        "파괴의 신": "God Tamer",
        # Items
        "영혼": "Soul",
        "마스크": "Mask",
        "참": "Charm",
        "지오": "Geo",
        "창백한 광석": "Pale Ore",
        # Locations
        "더트마우스": "Dirtmouth",
        "잊혀진 교차로": "Forgotten Crossroads",
        "초록길": "Greenpath",
        "곰팡이 황무지": "Fungal Wastes",
        "수정 봉우리": "Crystal Peak",
        "울부짖는 절벽": "Howling Cliffs",
        "꿈의 왕국": "White Palace",
        # Mechanics
        "대시": "Dash",
        "포고": "Pogo",
        "쉐이드": "Shade",
    },
    "silksong": {
        # Known entities
        "호넷": "Hornet",
        "레이스": "Lace",
        "세스": "Seth",
        "실크": "Silk",
        "파라스": "Pharloom",
    },
    "lies-of-p": {
        # Bosses
        "퍼레이드 마스터": "Parade Master",
        "스크라프드 워치맨": "Scrapped Watchman",
        "킹 오브 퍼펫": "King of Puppets",
        "로미오": "Romeo",
        "빅터": "Victor",
        "사이먼": "Simon Manus",
        "라신": "Laxasia",
        "네임리스 인형": "Nameless Puppet",
        # Items
        "에르고": "Ergo",
        "스타게이저": "Stargazer",
        "리전 암": "Legion Arm",
        "펄스 셀": "Pulse Cell",
        # Mechanics
        "거짓말": "Lie",
        "퍼펙트 가드": "Perfect Guard",
        "페이탈 어택": "Fatal Attack",
        "인간성": "Humanity",
    },
    # Dark Souls 시리즈
    "dark-souls": {
        # Bosses
        "아르토리아스": "Artorias",
        "시프": "Sif",
        "온스타인": "Ornstein",
        "스모우": "Smough",
        "귄도린": "Gwyndolin",
        "퀄라그": "Quelaag",
        "니토": "Nito",
        "시스": "Seath",
        "4인의 왕": "Four Kings",
        "가고일": "Gargoyle",
        "카프라 데몬": "Capra Demon",
        "타우르스 데몬": "Taurus Demon",
        "검은 용": "Black Dragon",
        "칼라미트": "Kalameet",
        "마누스": "Manus",
        "프리실라": "Priscilla",
        # Items
        "에스트 플라스크": "Estus Flask",
        "인간성": "Humanity",
        "소울": "Soul",
        "타이타나이트": "Titanite",
        "원시 결정": "Slab",
        # Locations
        "화염의 제사장": "Firelink Shrine",
        "불사의 소굴": "Undead Burg",
        "어노르 론도": "Anor Londo",
        "혼돈의 폐허": "Lost Izalith",
        "묘지": "Catacombs",
        "어둠의 심연": "Abyss",
        # Mechanics
        "패링": "Parry",
        "백스탭": "Backstab",
        "롤링": "Rolling",
        "이스턴스 프레임": "i-frames",
    },
    "dark-souls-2": {
        # Bosses
        "추적자": "Pursuer",
        "루인 센티넬": "Ruin Sentinels",
        "벨스타드": "Velstadt",
        "프루메 나이트": "Fume Knight",
        "알론": "Alonne",
        "미라의 루카티엘": "Lucatiel",
        "알디아": "Aldia",
        "내쉔드라": "Nashandra",
        "아이보리 킹": "Ivory King",
        "생크": "Sinh",
        "엘라나": "Elana",
        # Items
        "에스트": "Estus",
        "소울": "Soul",
        "효과의 조각": "Soul Memory",
        "인간의 형상": "Human Effigy",
        "귀향의 뼈": "Homeward Bone",
        # Locations
        "마슬라": "Majula",
        "용의 제단": "Dragon Aerie",
        "불꽃의 탑": "Iron Keep",
        "암흑의 협곡": "Black Gulch",
        # Mechanics
        "어댑터빌리티": "Adaptability",
        "파워 스탠스": "Power Stance",
    },
    "dark-souls-3": {
        # Bosses
        "군다": "Gundyr",
        "보르트": "Vordt",
        "술라": "Sulyvahn",
        "알드리치": "Aldrich",
        "무명왕": "Nameless King",
        "소울 오브 신더": "Soul of Cinder",
        "심연의 감시자": "Abyss Watchers",
        "프리드": "Friede",
        "게일": "Gael",
        "미디르": "Midir",
        "마녀 레이디": "Dancer",
        "쌍왕자": "Twin Princes",
        "오셀로트": "Oceiros",
        "요름": "Yhorm",
        "카스": "Champion's Gravetender",
        # Items
        "에스트": "Estus",
        "잿불": "Ember",
        "불씨": "Ember",
        "타이타나이트": "Titanite",
        "소울": "Soul",
        "원반": "Undead Bone Shard",
        "죽음의 반지": "Untrue Dark Ring",
        # Locations
        "화염의 제사장": "Firelink Shrine",
        "로델릭 고성": "High Wall",
        "이리실": "Irithyll",
        "아노르 론도": "Anor Londo",
        "드래그의 휴식지": "Archdragon Peak",
        "기억을 꾸는 도시": "Ringed City",
        # Mechanics
        "무기 기술": "Weapon Art",
        "FP": "Focus Points",
        "패링": "Parry",
        "백스탭": "Backstab",
        "출혈": "Bleed",
        "프로스트": "Frost",
    },
}


class EntityDictionary:
    """Korean-English entity mapping for game terms."""

    def __init__(self, game_id: str):
        self.game_id = game_id
        self.ko_to_en = ENTITY_DICTS.get(game_id, {})
        self.en_to_ko = {v: k for k, v in self.ko_to_en.items()}

    def translate_to_english(self, text: str) -> str:
        """Replace Korean entities with English equivalents."""
        result = text
        for ko, en in sorted(self.ko_to_en.items(), key=lambda x: -len(x[0])):
            result = result.replace(ko, en)
        return result

    def translate_to_korean(self, text: str) -> str:
        """Replace English entities with Korean equivalents."""
        result = text
        for en, ko in sorted(self.en_to_ko.items(), key=lambda x: -len(x[0])):
            # Case-insensitive replacement
            pattern = re.compile(re.escape(en), re.IGNORECASE)
            result = pattern.sub(ko, result)
        return result

    def extract_entities(self, text: str) -> list[str]:
        """Extract all recognized entities from text."""
        entities = []
        text_lower = text.lower()

        for ko, en in self.ko_to_en.items():
            if ko in text or en.lower() in text_lower:
                entities.append(en)

        return list(set(entities))

    def format_bilingual(self, entity: str) -> str:
        """Format entity as '한국어(English)' or 'English(한국어)'."""
        if entity in self.ko_to_en:
            return f"{entity}({self.ko_to_en[entity]})"
        elif entity in self.en_to_ko:
            return f"{self.en_to_ko[entity]}({entity})"
        return entity

    def expand_query(self, query: str) -> list[str]:
        """
        Expand query to include both Korean and English variants.

        Returns:
            List of queries [original, english_version]
        """
        queries = [query]
        english_query = self.translate_to_english(query)
        if english_query != query:
            queries.append(english_query)
        return queries


@lru_cache()
def get_entity_dictionary(game_id: str) -> EntityDictionary:
    """Get EntityDictionary for a game."""
    return EntityDictionary(game_id)
