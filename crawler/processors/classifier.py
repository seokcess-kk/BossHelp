"""Category Classifier for BossHelp Data Pipeline.

7개 카테고리로 문서를 분류하고 스포일러 레벨을 감지합니다.
"""

import re
from dataclasses import dataclass

from crawler.models import (
    CleanedDocument,
    ClassifiedDocument,
    Category,
    SpoilerLevel,
)


@dataclass
class ClassificationRule:
    """분류 규칙."""
    category: Category
    keywords: list[str]
    title_keywords: list[str]
    weight: float = 1.0


class CategoryClassifier:
    """카테고리 분류기."""

    # 카테고리별 분류 규칙
    RULES: list[ClassificationRule] = [
        ClassificationRule(
            category=Category.BOSS_GUIDE,
            keywords=[
                "boss", "보스", "defeat", "kill", "beat", "공략", "패턴",
                "phase", "페이즈", "attack", "dodge", "회피", "weakness", "약점",
                "strategy", "전략", "moveset", "기술", "hitbox",
            ],
            title_keywords=[
                "boss", "보스", "guide", "공략", "how to beat", "어떻게",
                "defeat", "kill", "tips for", "strategy",
            ],
            weight=1.2,
        ),
        ClassificationRule(
            category=Category.BUILD_GUIDE,
            keywords=[
                "build", "빌드", "stats", "스탯", "level", "레벨",
                "weapon", "무기", "armor", "방어구", "skill", "스킬",
                "attribute", "attribute", "faith", "신앙", "strength", "근력",
                "dexterity", "기량", "intelligence", "지력", "arcane", "신비",
                "bleed", "출혈", "frost", "냉기", "fire", "화염",
            ],
            title_keywords=[
                "build", "빌드", "best", "최강", "op", "meta", "tier",
            ],
            weight=1.1,
        ),
        ClassificationRule(
            category=Category.PROGRESSION_ROUTE,
            keywords=[
                "order", "순서", "route", "루트", "walkthrough", "진행",
                "first", "먼저", "after", "다음", "before", "이전",
                "path", "경로", "area", "지역", "recommended", "추천",
                "early game", "초반", "mid game", "중반", "late game", "후반",
            ],
            title_keywords=[
                "order", "순서", "route", "루트", "walkthrough", "where to go",
                "어디", "progression", "진행",
            ],
            weight=1.0,
        ),
        ClassificationRule(
            category=Category.NPC_QUEST,
            keywords=[
                "npc", "quest", "퀘스트", "questline", "dialogue", "대화",
                "ending", "엔딩", "summon", "소환", "location", "위치",
                "trigger", "트리거", "choice", "선택", "outcome", "결과",
            ],
            title_keywords=[
                "quest", "퀘스트", "npc", "ending", "엔딩", "questline",
            ],
            weight=1.0,
        ),
        ClassificationRule(
            category=Category.ITEM_LOCATION,
            keywords=[
                "location", "위치", "where", "어디", "find", "찾기",
                "drop", "드랍", "loot", "획득", "chest", "상자",
                "hidden", "숨겨진", "secret", "비밀", "collect", "수집",
                "talisman", "탈리스만", "ring", "반지", "charm", "참",
            ],
            title_keywords=[
                "location", "위치", "where", "어디", "find", "how to get",
            ],
            weight=1.0,
        ),
        ClassificationRule(
            category=Category.MECHANIC_TIP,
            keywords=[
                "mechanic", "메카닉", "system", "시스템", "how", "방법",
                "tip", "팁", "trick", "트릭", "tech", "테크닉",
                "parry", "패링", "deflect", "튕기기", "jump", "점프",
                "roll", "구르기", "iframe", "무적", "stamina", "스태미나",
            ],
            title_keywords=[
                "tip", "팁", "trick", "how to", "mechanic", "guide",
                "tutorial", "튜토리얼", "basics", "기초",
            ],
            weight=0.9,
        ),
        ClassificationRule(
            category=Category.SECRET_HIDDEN,
            keywords=[
                "secret", "비밀", "hidden", "숨겨진", "easter egg", "이스터에그",
                "rare", "희귀", "missable", "놓치기", "optional", "선택적",
                "lore", "로어", "backstory", "배경", "theory", "이론",
            ],
            title_keywords=[
                "secret", "비밀", "hidden", "숨겨진", "rare", "missable",
            ],
            weight=0.9,
        ),
    ]

    # 스포일러 감지 키워드
    HEAVY_SPOILER_KEYWORDS = [
        "ending", "엔딩", "final boss", "최종 보스", "true ending", "진엔딩",
        "secret ending", "비밀 엔딩", "death", "죽음", "betrayal", "배신",
        "plot twist", "반전", "revelation", "reveal",
    ]

    LIGHT_SPOILER_KEYWORDS = [
        "boss", "보스", "area", "지역", "npc", "quest", "퀘스트",
        "item", "아이템", "weapon", "무기",
    ]

    # 게임별 엔티티 (일부)
    ENTITY_PATTERNS: dict[str, list[str]] = {
        "elden-ring": [
            r"Malenia|말레니아", r"Radahn|라단", r"Margit|마르기트",
            r"Godrick|고드릭", r"Ranni|라니", r"Melina|멜리나",
            r"Mimic Tear|미믹의 눈물", r"Rivers of Blood|피의 강",
        ],
        "sekiro": [
            r"Genichiro|겐이치로", r"Isshin|이신", r"Owl|올빼미",
            r"Guardian Ape|수호원숭이", r"Mikiri|미키리",
        ],
        "hollow-knight": [
            r"Radiance|레이디언스", r"Hornet|호넷", r"Grimm|그림",
            r"Nail|네일", r"Charm|참", r"Pale King|창백한 왕",
        ],
        "lies-of-p": [
            r"Pinocchio|피노키오", r"Geppetto|제페토",
            r"Parade Master|퍼레이드 마스터", r"Ergo|에르고",
        ],
    }

    def classify(self, doc: CleanedDocument) -> ClassifiedDocument:
        """
        문서 분류.

        1. 카테고리 분류 (키워드 기반)
        2. 스포일러 레벨 감지
        3. 엔티티 태그 추출
        """
        text = f"{doc.title} {doc.content}".lower()

        # 카테고리 분류
        category, confidence = self._classify_category(doc.title, doc.content)

        # 스포일러 레벨 감지
        spoiler_level = self._detect_spoiler_level(text)

        # 엔티티 태그 추출
        entity_tags = self._extract_entities(doc.game_id, text)

        return ClassifiedDocument(
            game_id=doc.game_id,
            source_type=doc.source_type,
            source_url=doc.source_url,
            title=doc.title,
            content=doc.content,
            category=category,
            category_confidence=confidence,
            spoiler_level=spoiler_level,
            entity_tags=entity_tags,
            upvotes=doc.upvotes,
            created_at=doc.created_at,
        )

    def classify_batch(
        self, docs: list[CleanedDocument]
    ) -> list[ClassifiedDocument]:
        """배치 분류."""
        return [self.classify(doc) for doc in docs]

    def _classify_category(
        self, title: str, content: str
    ) -> tuple[Category, float]:
        """카테고리 분류."""
        title_lower = title.lower()
        content_lower = content.lower()
        full_text = f"{title_lower} {content_lower}"

        scores: dict[Category, float] = {}

        for rule in self.RULES:
            score = 0.0

            # 제목 키워드 매칭 (가중치 높음)
            for keyword in rule.title_keywords:
                if keyword.lower() in title_lower:
                    score += 3.0 * rule.weight

            # 본문 키워드 매칭
            for keyword in rule.keywords:
                count = full_text.count(keyword.lower())
                score += min(count * 0.5, 3.0) * rule.weight

            scores[rule.category] = score

        # 최고 점수 카테고리 선택
        if not scores or max(scores.values()) == 0:
            return Category.MECHANIC_TIP, 0.5

        best_category = max(scores, key=scores.get)
        total_score = sum(scores.values())
        confidence = scores[best_category] / total_score if total_score > 0 else 0.5

        return best_category, min(confidence, 1.0)

    def _detect_spoiler_level(self, text: str) -> SpoilerLevel:
        """스포일러 레벨 감지."""
        text_lower = text.lower()

        # Heavy 스포일러 체크
        for keyword in self.HEAVY_SPOILER_KEYWORDS:
            if keyword.lower() in text_lower:
                return SpoilerLevel.HEAVY

        # Light 스포일러 체크
        for keyword in self.LIGHT_SPOILER_KEYWORDS:
            if keyword.lower() in text_lower:
                return SpoilerLevel.LIGHT

        return SpoilerLevel.NONE

    def _extract_entities(self, game_id: str, text: str) -> list[str]:
        """엔티티 태그 추출."""
        entities: set[str] = set()
        patterns = self.ENTITY_PATTERNS.get(game_id, [])

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # 정규화된 형태로 저장
                entities.add(match.lower())

        return list(entities)[:10]  # 최대 10개
