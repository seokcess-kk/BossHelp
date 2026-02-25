# Entity Tagging Improvement Design

> 청크 레벨 엔티티 태깅 개선을 통한 RAG 검색 정확도 향상 상세 설계

## Overview

| Item | Value |
|------|-------|
| Feature | entity-tagging-improvement |
| Phase | Design |
| Created | 2026-02-25 |
| Plan Document | `docs/01-plan/features/entity-tagging-improvement.plan.md` |
| Status | In Progress |

---

## 1. Current Architecture Analysis

### 1.1 Entity Tagging Flow (As-Is)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Current Entity Tagging                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [Crawler: Wiki Page]                                                   │
│     │                                                                   │
│     ▼                                                                   │
│  ┌─────────────┐                                                        │
│  │ Page Parse  │ ← 전체 페이지에서 엔티티 추출                          │
│  │             │   (모든 청크에 동일 태그 적용)                          │
│  └──────┬──────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ entity_tags = ['malenia', 'radahn', 'ranni', 'rivers of blood'] │   │
│  │         ↓                                                        │   │
│  │   Chunk 1: "Malenia Phase 1..."  → Same tags ❌                  │   │
│  │   Chunk 2: "Malenia Phase 2..."  → Same tags ❌                  │   │
│  │   Chunk 3: "Related Bosses..."   → Same tags ❌                  │   │
│  │   Chunk 4: "See also Radahn..."  → Same tags ❌                  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  문제점:                                                                │
│  - Chunk 3, 4도 Malenia 태그 보유 → 검색 오매칭                         │
│  - primary_entity 없음 → 출처 품질 판단 불가                            │
│  - entity_type 없음 → 보스/무기/장소 구분 불가                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Current Database Schema

```sql
-- chunks 테이블 (현재)
CREATE TABLE chunks (
    id UUID PRIMARY KEY,
    game_id TEXT NOT NULL,
    category TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_url TEXT NOT NULL,
    title TEXT,                    -- "Malenia Blade of Miquella | Elden Ring Wiki"
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    quality_score FLOAT,
    spoiler_level TEXT,
    entity_tags TEXT[] DEFAULT '{}',  -- 페이지 레벨 (정확도 낮음)
    -- primary_entity 없음 ❌
    -- entity_type 없음 ❌
    ...
);
```

### 1.3 Current Files & Modules

| File | Lines | Purpose | Key Classes/Functions |
|------|:-----:|---------|----------------------|
| `backend/app/core/entity/auto_extractor.py` | 158 | 제목에서 엔티티 추출 | `EntityAutoExtractor` |
| `backend/app/core/entity/dictionary.py` | 342 | 한영 엔티티 사전 | `EntityDictionary` |
| `backend/app/core/rag/retriever.py` | 261 | 벡터 검색 | `VectorRetriever` |
| `supabase/migrations/001_initial_schema.sql` | 182 | DB 스키마 | chunks 테이블 |

### 1.4 Identified Issues

| Issue | Impact | Root Cause |
|-------|--------|------------|
| 페이지 레벨 태깅 | 엔티티 필터링 정확도 70% | 청크별 태그 미분리 |
| primary_entity 없음 | 출처 품질 저하 | 주 엔티티 식별 로직 부재 |
| entity_type 없음 | 카테고리 부스팅 불가 | 유형 분류 로직 부재 |
| 47K 청크 중 ~100개 유니크 태그 조합 | 세밀한 검색 불가 | 다양성 부족 |

---

## 2. Architecture Design (To-Be)

### 2.1 Enhanced Entity Tagging Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Enhanced Entity Tagging                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [Title + Category]                                                     │
│     │                                                                   │
│     ▼                                                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              TitleEntityExtractor                                │   │
│  │                                                                  │   │
│  │  Input: "Malenia Blade of Miquella | Elden Ring Wiki"            │   │
│  │                                                                  │   │
│  │  Pattern: ^(.+?)\s*\|\s*(?:Elden Ring|...).*Wiki                 │   │
│  │                                                                  │   │
│  │  Output:                                                         │   │
│  │    primary_entity = "Malenia Blade of Miquella"                  │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              EntityTypeClassifier                                │   │
│  │                                                                  │   │
│  │  Input:                                                          │   │
│  │    - entity_name: "Malenia Blade of Miquella"                    │   │
│  │    - category: "boss_guide"                                      │   │
│  │                                                                  │   │
│  │  Rules:                                                          │   │
│  │    1. category = boss_guide → type = "boss"                      │   │
│  │    2. Keywords: "Sword", "Katana" → type = "weapon"              │   │
│  │    3. Keywords: "Castle", "Ruins" → type = "location"            │   │
│  │                                                                  │   │
│  │  Output:                                                         │   │
│  │    entity_type = "boss"                                          │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Updated Chunk                               │   │
│  │                                                                  │   │
│  │  {                                                               │   │
│  │    "title": "Malenia Blade of Miquella | Elden Ring Wiki",       │   │
│  │    "primary_entity": "Malenia Blade of Miquella",   ← NEW        │   │
│  │    "entity_type": "boss",                           ← NEW        │   │
│  │    "entity_tags": ["malenia", "radahn", ...]                     │   │
│  │  }                                                               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Enhanced Search Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Enhanced RAG Search                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  [Query: "말레니아 공략"]                                               │
│     │                                                                   │
│     ▼                                                                   │
│  ┌─────────────┐                                                        │
│  │ Translation │ → "Malenia guide"                                     │
│  └──────┬──────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────┐                                                        │
│  │   Entity    │ → entities = ["Malenia"]                              │
│  │ Extraction  │   question_type = "boss_guide"                        │
│  └──────┬──────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │            Step 1: Entity Pre-filter (NEW)                       │   │
│  │                                                                  │   │
│  │  SELECT * FROM chunks                                            │   │
│  │  WHERE primary_entity ILIKE '%Malenia%'                          │   │
│  │     OR 'malenia' = ANY(entity_tags)                              │   │
│  │                                                                  │   │
│  │  Result: ~500 chunks (vs 47,000 전체)                            │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │            Step 2: primary_entity Boost (NEW)                    │   │
│  │                                                                  │   │
│  │  - primary_entity = "Malenia" → boost × 1.5                      │   │
│  │  - entity_type = "boss" (질문이 boss_guide) → boost × 1.3        │   │
│  │  - entity_tags contains "malenia" → boost × 1.1                  │   │
│  │                                                                  │   │
│  │  Priority:                                                       │   │
│  │    1. Malenia 전용 페이지 청크 (primary_entity 일치)             │   │
│  │    2. Malenia 언급된 다른 페이지 청크 (entity_tags)              │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────┐                                                        │
│  │   Vector    │ ← 필터링된 500개 청크에서만 벡터 검색               │
│  │   Search    │                                                       │
│  └──────┬──────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│  ┌─────────────┐                                                        │
│  │   Rerank    │                                                        │
│  │   (top 5)   │                                                        │
│  └──────┬──────┘                                                        │
│         │                                                               │
│         ▼                                                               │
│      [Answer]                                                           │
│                                                                         │
│  예상 효과:                                                             │
│  - 검색 대상: 47,000 → 500 (90% 감소)                                  │
│  - 응답 시간: 8-15초 → 3-5초                                           │
│  - 정확도: 70% → 95%+                                                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.3 Component Design

#### 2.3.1 TitleEntityExtractor

**New File:** `backend/app/core/entity/title_extractor.py`

```python
"""Title-based Entity Extractor."""

import re
from dataclasses import dataclass


@dataclass
class ExtractedEntity:
    """추출된 엔티티 정보."""
    name: str
    normalized: str  # lowercase, trimmed


class TitleEntityExtractor:
    """Title에서 주 엔티티 추출.

    Wiki 제목 패턴을 분석하여 해당 페이지의 주제(primary entity)를 식별.
    """

    # Wiki 제목 패턴 (게임별)
    WIKI_PATTERNS = [
        # "Malenia Blade of Miquella | Elden Ring Wiki"
        r"^(.+?)\s*\|\s*(?:Elden Ring|Dark Souls|Sekiro|Hollow Knight|Lies of P)[^|]*Wiki",
        # "Malenia Blade of Miquella - Elden Ring Wiki Guide"
        r"^(.+?)\s*-\s*(?:Elden Ring|Dark Souls|Sekiro)[^-]*(?:Wiki|Guide)",
        # "Malenia Blade of Miquella" (단순 제목)
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
    ]

    def extract(self, title: str) -> ExtractedEntity | None:
        """
        Title에서 primary entity 추출.

        Args:
            title: 청크 제목

        Returns:
            ExtractedEntity or None if extraction failed

        Examples:
            >>> extractor = TitleEntityExtractor()
            >>> extractor.extract("Malenia Blade of Miquella | Elden Ring Wiki")
            ExtractedEntity(name="Malenia Blade of Miquella", normalized="malenia blade of miquella")

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

        return ExtractedEntity(
            name=entity_name,
            normalized=entity_name.lower().strip(),
        )

    def _should_exclude(self, name: str) -> bool:
        """제외 대상 확인."""
        for pattern in self.EXCLUDE_PATTERNS:
            if re.match(pattern, name, re.IGNORECASE):
                return True
        return False


# Singleton
_extractor: TitleEntityExtractor | None = None


def get_title_extractor() -> TitleEntityExtractor:
    """TitleEntityExtractor 싱글톤."""
    global _extractor
    if _extractor is None:
        _extractor = TitleEntityExtractor()
    return _extractor
```

#### 2.3.2 EntityTypeClassifier

**New File:** `backend/app/core/entity/type_classifier.py`

```python
"""Entity Type Classifier."""

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
    TYPE_KEYWORDS = {
        EntityType.BOSS: [
            "Demigod", "Lord", "King", "Queen", "Knight", "Dragon",
            "Omen", "Beast", "God", "Godfrey", "Radagon", "Maliketh",
            "Grafted", "Champion", "Apostle", "Sentinel", "Giant",
        ],
        EntityType.WEAPON: [
            "Sword", "Katana", "Blade", "Staff", "Seal", "Shield",
            "Bow", "Crossbow", "Spear", "Halberd", "Axe", "Hammer",
            "Dagger", "Claw", "Fist", "Whip", "Scythe", "Flail",
            "Greatsword", "Colossal", "Twinblade",
        ],
        EntityType.ARMOR: [
            "Armor", "Helm", "Helmet", "Gauntlets", "Greaves",
            "Set", "Robe", "Cloak", "Mask", "Hood", "Crown",
        ],
        EntityType.LOCATION: [
            "Castle", "Ruins", "Dungeon", "Cave", "Catacombs",
            "Tower", "Palace", "Temple", "Shrine", "Gate",
            "Valley", "Lake", "Mountain", "Plateau", "Grave",
        ],
        EntityType.NPC: [
            "Merchant", "Maiden", "Finger", "Tarnished",
            "Witch", "Sorcerer", "Prophet", "Warrior",
        ],
        EntityType.ITEM: [
            "Talisman", "Ring", "Amulet", "Key", "Bell",
            "Rune", "Stone", "Flask", "Tear", "Crystal",
        ],
        EntityType.SPELL: [
            "Incantation", "Sorcery", "Spell", "Ash of War",
            "Skill", "Art",
        ],
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
            EntityType.WEAPON  # "Blade" 키워드 없지만 알려진 무기
        """
        # 1. 카테고리 기반 우선 분류
        if category and category in self.CATEGORY_MAPPING:
            return self.CATEGORY_MAPPING[category]

        # 2. 키워드 기반 분류
        entity_upper = entity_name
        for entity_type, keywords in self.TYPE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in entity_upper:
                    return entity_type

        # 3. 알려진 엔티티 사전 (하드코딩)
        known_types = self._get_known_entity_type(entity_name)
        if known_types:
            return known_types

        return EntityType.UNKNOWN

    def _get_known_entity_type(self, entity_name: str) -> EntityType | None:
        """알려진 엔티티 유형 조회 (사전 기반)."""
        # 주요 보스
        known_bosses = {
            "malenia", "radahn", "morgott", "mohg", "rykard",
            "godrick", "rennala", "radagon", "maliketh", "placidusax",
            "godfrey", "hoarah loux", "elden beast", "margit",
        }

        # 주요 무기
        known_weapons = {
            "moonveil", "rivers of blood", "blasphemous blade",
            "dark moon greatsword", "starscourge greatsword",
            "sword of night and flame", "wing of astel",
        }

        # 주요 NPC
        known_npcs = {
            "ranni", "melina", "alexander", "patches", "blaidd",
            "fia", "goldmask", "nepheli", "kenneth", "hyetta",
        }

        name_lower = entity_name.lower()

        for boss in known_bosses:
            if boss in name_lower:
                return EntityType.BOSS

        for weapon in known_weapons:
            if weapon in name_lower:
                return EntityType.WEAPON

        for npc in known_npcs:
            if npc in name_lower:
                return EntityType.NPC

        return None


# Singleton
_classifier: EntityTypeClassifier | None = None


def get_type_classifier() -> EntityTypeClassifier:
    """EntityTypeClassifier 싱글톤."""
    global _classifier
    if _classifier is None:
        _classifier = EntityTypeClassifier()
    return _classifier
```

#### 2.3.3 Migration Script

**New File:** `crawler/migrate_entity_tags.py`

```python
"""Entity Tags Migration Script.

기존 47,073개 청크에 primary_entity, entity_type 추가.
"""

import asyncio
import logging
from tqdm import tqdm
from supabase import create_client
from dotenv import load_dotenv
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.core.entity.title_extractor import get_title_extractor
from app.core.entity.type_classifier import get_type_classifier, EntityType

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate_all_chunks(
    batch_size: int = 100,
    dry_run: bool = False,
) -> dict:
    """
    기존 청크에 primary_entity, entity_type 추가.

    Args:
        batch_size: 배치 처리 크기
        dry_run: True면 실제 업데이트 없이 시뮬레이션

    Returns:
        Migration 결과 통계
    """
    # Supabase 클라이언트
    supabase = create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_SERVICE_KEY"),
    )

    extractor = get_title_extractor()
    classifier = get_type_classifier()

    # 전체 청크 수 조회
    count_result = supabase.table("chunks").select(
        "id", count="exact"
    ).eq("is_active", True).execute()

    total_count = count_result.count
    logger.info(f"Total chunks to migrate: {total_count}")

    stats = {
        "total": total_count,
        "processed": 0,
        "success": 0,
        "no_entity": 0,
        "errors": 0,
        "type_distribution": {},
    }

    # 배치 처리
    offset = 0
    with tqdm(total=total_count, desc="Migrating") as pbar:
        while offset < total_count:
            # 배치 조회
            result = supabase.table("chunks").select(
                "id", "title", "category"
            ).eq("is_active", True).range(
                offset, offset + batch_size - 1
            ).execute()

            if not result.data:
                break

            for chunk in result.data:
                try:
                    chunk_id = chunk["id"]
                    title = chunk.get("title", "")
                    category = chunk.get("category", "")

                    # 엔티티 추출
                    entity = extractor.extract(title)

                    if entity:
                        # 유형 분류
                        entity_type = classifier.classify(
                            entity.name, category
                        )

                        # 업데이트 데이터
                        update_data = {
                            "primary_entity": entity.name,
                            "entity_type": entity_type.value,
                        }

                        # 실제 업데이트 (dry_run이 아닐 때만)
                        if not dry_run:
                            supabase.table("chunks").update(
                                update_data
                            ).eq("id", chunk_id).execute()

                        stats["success"] += 1

                        # 유형 통계
                        type_name = entity_type.value
                        stats["type_distribution"][type_name] = \
                            stats["type_distribution"].get(type_name, 0) + 1
                    else:
                        stats["no_entity"] += 1

                    stats["processed"] += 1

                except Exception as e:
                    logger.error(f"Error processing chunk {chunk_id}: {e}")
                    stats["errors"] += 1

                pbar.update(1)

            offset += batch_size

    return stats


def main():
    """CLI 엔트리포인트."""
    import argparse

    parser = argparse.ArgumentParser(description="Migrate entity tags")
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--dry-run", action="store_true")

    args = parser.parse_args()

    logger.info(f"Starting migration (dry_run={args.dry_run})")

    stats = asyncio.run(migrate_all_chunks(
        batch_size=args.batch_size,
        dry_run=args.dry_run,
    ))

    logger.info("Migration completed!")
    logger.info(f"Stats: {stats}")

    # 유형별 분포 출력
    print("\nEntity Type Distribution:")
    for entity_type, count in sorted(
        stats["type_distribution"].items(),
        key=lambda x: x[1],
        reverse=True
    ):
        print(f"  {entity_type}: {count}")


if __name__ == "__main__":
    main()
```

---

## 3. Database Schema Changes

### 3.1 New Columns

```sql
-- 005_entity_tagging.sql

-- 1. 새 컬럼 추가
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS primary_entity TEXT;
ALTER TABLE chunks ADD COLUMN IF NOT EXISTS entity_type TEXT;

-- 2. entity_type 제약조건
ALTER TABLE chunks ADD CONSTRAINT chk_entity_type
    CHECK (entity_type IS NULL OR entity_type IN (
        'boss', 'weapon', 'armor', 'location',
        'npc', 'item', 'spell', 'mechanic', 'unknown'
    ));

-- 3. 검색 성능을 위한 인덱스
CREATE INDEX IF NOT EXISTS idx_chunks_primary_entity
    ON chunks(primary_entity)
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_chunks_entity_type
    ON chunks(entity_type)
    WHERE is_active = true;

-- 4. primary_entity 부분 검색용 인덱스 (trigram)
CREATE INDEX IF NOT EXISTS idx_chunks_primary_entity_trgm
    ON chunks USING gin (primary_entity gin_trgm_ops)
    WHERE is_active = true;

-- 5. 복합 인덱스 (game + entity_type)
CREATE INDEX IF NOT EXISTS idx_chunks_game_entity_type
    ON chunks(game_id, entity_type)
    WHERE is_active = true;
```

### 3.2 Updated Schema Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          chunks (Updated)                               │
├─────────────────────────────────────────────────────────────────────────┤
│ id                UUID         PK                                       │
│ game_id           TEXT         FK → games.id                            │
│ category          TEXT         CHECK (...)                              │
│ source_type       TEXT         CHECK (...)                              │
│ source_url        TEXT         NOT NULL                                 │
│ title             TEXT                                                  │
│ content           TEXT         NOT NULL                                 │
│ embedding         VECTOR(1536)                                          │
│ quality_score     FLOAT        0~1                                      │
│ spoiler_level     TEXT         none/light/heavy                         │
│ entity_tags       TEXT[]       페이지 레벨 태그 (기존 유지)              │
│ ──────────────────────────────────────────────────────────────────────  │
│ primary_entity    TEXT         NEW: 주 엔티티명                          │
│ entity_type       TEXT         NEW: boss/weapon/location/...            │
│ ──────────────────────────────────────────────────────────────────────  │
│ patch_version     TEXT                                                  │
│ is_active         BOOLEAN      default true                             │
│ feedback_helpful  INT          default 0                                │
│ created_at        TIMESTAMPTZ                                           │
│ updated_at        TIMESTAMPTZ                                           │
└─────────────────────────────────────────────────────────────────────────┘

Indexes:
  - idx_chunks_primary_entity (B-tree)
  - idx_chunks_entity_type (B-tree)
  - idx_chunks_primary_entity_trgm (GIN trigram)
  - idx_chunks_game_entity_type (Composite B-tree)
```

---

## 4. Retriever Enhancement

### 4.1 Modified VectorRetriever

**Modified File:** `backend/app/core/rag/retriever.py`

```python
# retriever.py 수정 부분

def search(
    self,
    embedding: list[float],
    game_id: str,
    spoiler_level: str = "none",
    category: str | None = None,
    limit: int = 10,
    threshold: float = 0.5,
    query: str = "",
    entities: list[str] | None = None,  # NEW: 추출된 엔티티
) -> list[dict]:
    """
    Search for similar chunks using vector similarity.

    NEW: entities 파라미터로 엔티티 기반 1차 필터링 수행.
    """
    spoiler_levels = self._get_allowed_spoiler_levels(spoiler_level)

    # NEW: 엔티티 기반 1차 필터링
    if entities:
        pre_filtered = self._filter_by_entities(
            game_id=game_id,
            entities=entities,
            spoiler_levels=spoiler_levels,
            limit=500,  # 1차 필터링 결과 최대 500개
        )

        if pre_filtered:
            # 필터링된 청크 ID 목록으로 벡터 검색 범위 제한
            chunk_ids = [c["id"] for c in pre_filtered]
            return self._search_within_ids(
                embedding=embedding,
                chunk_ids=chunk_ids,
                limit=limit,
            )

    # 기존 로직 (엔티티 없을 때)
    return self._full_vector_search(...)


def _filter_by_entities(
    self,
    game_id: str,
    entities: list[str],
    spoiler_levels: list[str],
    limit: int = 500,
) -> list[dict]:
    """
    엔티티 기반 1차 필터링.

    우선순위:
    1. primary_entity 완전 일치
    2. primary_entity 부분 일치
    3. entity_tags 포함
    """
    results = []

    for entity in entities:
        entity_lower = entity.lower()

        # 1. primary_entity 완전 일치
        exact_match = self.client.table("chunks").select(
            "id", "title", "primary_entity", "entity_type", "quality_score"
        ).eq("game_id", game_id).eq("is_active", True).in_(
            "spoiler_level", spoiler_levels
        ).ilike("primary_entity", entity_lower).limit(100).execute()

        results.extend(exact_match.data or [])

        # 2. primary_entity 부분 일치
        if len(results) < limit:
            partial_match = self.client.table("chunks").select(
                "id", "title", "primary_entity", "entity_type", "quality_score"
            ).eq("game_id", game_id).eq("is_active", True).in_(
                "spoiler_level", spoiler_levels
            ).ilike("primary_entity", f"%{entity_lower}%").limit(100).execute()

            # 중복 제거
            existing_ids = {r["id"] for r in results}
            for r in partial_match.data or []:
                if r["id"] not in existing_ids:
                    results.append(r)

        # 3. entity_tags 포함
        if len(results) < limit:
            tags_match = self.client.table("chunks").select(
                "id", "title", "primary_entity", "entity_type", "quality_score"
            ).eq("game_id", game_id).eq("is_active", True).in_(
                "spoiler_level", spoiler_levels
            ).contains("entity_tags", [entity_lower]).limit(100).execute()

            existing_ids = {r["id"] for r in results}
            for r in tags_match.data or []:
                if r["id"] not in existing_ids:
                    results.append(r)

    return results[:limit]


def _apply_entity_boost(
    self,
    chunks: list[dict],
    entities: list[str],
) -> list[dict]:
    """
    엔티티 매칭 기반 점수 부스트.

    NEW: primary_entity 일치 시 더 높은 부스트.
    """
    for chunk in chunks:
        primary_entity = (chunk.get("primary_entity") or "").lower()
        entity_tags = [t.lower() for t in chunk.get("entity_tags", [])]

        boost = 0.0

        for entity in entities:
            entity_lower = entity.lower()

            # primary_entity 완전 일치: +0.3
            if entity_lower in primary_entity or primary_entity in entity_lower:
                boost += 0.3
            # entity_tags 포함: +0.1
            elif entity_lower in entity_tags:
                boost += 0.1

        current_similarity = chunk.get("similarity", 0.5)
        chunk["similarity"] = min(1.0, current_similarity + boost)
        chunk["entity_boosted"] = boost > 0

    return chunks
```

---

## 5. API Specification

### 5.1 Updated RPC Function

**Modified File:** `supabase/migrations/002_search_function.sql` → `006_enhanced_search.sql`

```sql
-- Enhanced search function with entity filtering
CREATE OR REPLACE FUNCTION search_chunks_v2(
    query_embedding VECTOR(1536),
    match_threshold FLOAT DEFAULT 0.3,
    match_count INT DEFAULT 10,
    filter_game_id TEXT DEFAULT NULL,
    filter_spoiler_levels TEXT[] DEFAULT ARRAY['none'],
    filter_category TEXT DEFAULT NULL,
    filter_entities TEXT[] DEFAULT NULL,      -- NEW
    filter_entity_type TEXT DEFAULT NULL,     -- NEW
    search_text TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    game_id TEXT,
    category TEXT,
    source_type TEXT,
    source_url TEXT,
    title TEXT,
    content TEXT,
    quality_score FLOAT,
    spoiler_level TEXT,
    entity_tags TEXT[],
    primary_entity TEXT,     -- NEW
    entity_type TEXT,        -- NEW
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        c.id,
        c.game_id,
        c.category,
        c.source_type,
        c.source_url,
        c.title,
        c.content,
        c.quality_score,
        c.spoiler_level,
        c.entity_tags,
        c.primary_entity,
        c.entity_type,
        1 - (c.embedding <=> query_embedding) AS similarity
    FROM chunks c
    WHERE
        c.is_active = true
        AND (filter_game_id IS NULL OR c.game_id = filter_game_id)
        AND c.spoiler_level = ANY(filter_spoiler_levels)
        AND (filter_category IS NULL OR c.category = filter_category)
        -- NEW: entity filtering
        AND (
            filter_entities IS NULL
            OR c.primary_entity ILIKE ANY(
                SELECT '%' || unnest(filter_entities) || '%'
            )
            OR c.entity_tags && filter_entities
        )
        AND (
            filter_entity_type IS NULL
            OR c.entity_type = filter_entity_type
        )
        AND (
            search_text IS NULL
            OR c.content ILIKE '%' || search_text || '%'
            OR c.title ILIKE '%' || search_text || '%'
        )
    ORDER BY
        -- Primary entity match boost
        CASE
            WHEN filter_entities IS NOT NULL
                 AND c.primary_entity ILIKE ANY(
                     SELECT '%' || unnest(filter_entities) || '%'
                 )
            THEN 0
            ELSE 1
        END,
        similarity DESC
    LIMIT match_count;
END;
$$;
```

### 5.2 Response Format Updates

No changes to API response format. Internal optimization only.

---

## 6. Implementation Order

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Implementation Phases                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Phase 1: Database Schema (Priority: Highest)                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 1.1 005_entity_tagging.sql 작성                                 │   │
│  │ 1.2 Supabase에서 마이그레이션 실행                               │   │
│  │ 1.3 인덱스 생성 확인                                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                          ↓                                              │
│  Phase 2: Entity Extraction Logic (Priority: High)                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 2.1 title_extractor.py 구현                                     │   │
│  │ 2.2 type_classifier.py 구현                                     │   │
│  │ 2.3 단위 테스트 작성                                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                          ↓                                              │
│  Phase 3: Data Migration (Priority: High)                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 3.1 migrate_entity_tags.py 구현                                 │   │
│  │ 3.2 Dry-run 테스트                                              │   │
│  │ 3.3 실제 마이그레이션 실행 (47,073개 청크)                       │   │
│  │ 3.4 결과 검증                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                          ↓                                              │
│  Phase 4: Retriever Enhancement (Priority: Medium)                     │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 4.1 retriever.py 수정 (_filter_by_entities)                     │   │
│  │ 4.2 search_chunks_v2 RPC 함수 생성                              │   │
│  │ 4.3 _apply_entity_boost 개선                                    │   │
│  │ 4.4 통합 테스트                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                          ↓                                              │
│  Phase 5: Testing & Validation (Priority: Medium)                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 5.1 엔티티 검색 정확도 측정                                      │   │
│  │ 5.2 응답 시간 벤치마크                                          │   │
│  │ 5.3 A/B 테스트 (선택)                                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 7. Testing Strategy

### 7.1 Unit Tests

| Test | File | Coverage |
|------|------|----------|
| 제목 파싱 | `test_title_extractor.py` | TitleEntityExtractor |
| 유형 분류 | `test_type_classifier.py` | EntityTypeClassifier |
| 마이그레이션 | `test_migration.py` | migrate_entity_tags |

### 7.2 Integration Tests

| Test | Scenario |
|------|----------|
| 엔티티 필터링 | "Malenia" 검색 → primary_entity 일치 청크 우선 |
| 벡터 + 엔티티 | 벡터 유사도 + 엔티티 부스트 통합 테스트 |
| 응답 시간 | 엔티티 필터링 vs 전체 검색 속도 비교 |

### 7.3 Test Cases

```python
# test_title_extractor.py

def test_extract_wiki_title():
    extractor = TitleEntityExtractor()

    # 정상 케이스
    result = extractor.extract("Malenia Blade of Miquella | Elden Ring Wiki")
    assert result.name == "Malenia Blade of Miquella"

    result = extractor.extract("Rivers of Blood | Elden Ring Wiki")
    assert result.name == "Rivers of Blood"

    # 제외 케이스
    result = extractor.extract("All Bosses | Elden Ring Wiki")
    assert result is None

    result = extractor.extract("Walkthrough | Elden Ring Wiki")
    assert result is None


def test_classify_entity_type():
    classifier = EntityTypeClassifier()

    assert classifier.classify(
        "Malenia Blade of Miquella", "boss_guide"
    ) == EntityType.BOSS

    assert classifier.classify(
        "Moonveil", "item_location"
    ) == EntityType.WEAPON  # 알려진 무기

    assert classifier.classify(
        "Redmane Castle", "progression_route"
    ) == EntityType.LOCATION
```

---

## 8. Performance Expectations

| Metric | Before | After | Improvement |
|--------|:------:|:-----:|:-----------:|
| 검색 대상 청크 | 47,073 | ~500 | 90% 감소 |
| 평균 응답 시간 | 8-15초 | 3-5초 | 60% 감소 |
| 엔티티 검색 정확도 | 70% | 95%+ | +25% |
| 1차 필터링 가능 | 0% | 80%+ | +80% |

---

## 9. Rollback Plan

| Phase | Rollback Method |
|-------|-----------------|
| Phase 1 (Schema) | `ALTER TABLE chunks DROP COLUMN primary_entity, entity_type` |
| Phase 2 (Extractor) | 새 파일 삭제, import 제거 |
| Phase 3 (Migration) | `UPDATE chunks SET primary_entity = NULL, entity_type = NULL` |
| Phase 4 (Retriever) | 기존 search 함수로 복원 |

---

## 10. Files to Create/Modify

### 10.1 New Files

| File | Purpose | Lines (Est.) |
|------|---------|:------------:|
| `backend/app/core/entity/title_extractor.py` | 제목 기반 엔티티 추출 | ~100 |
| `backend/app/core/entity/type_classifier.py` | 엔티티 유형 분류 | ~120 |
| `crawler/migrate_entity_tags.py` | 마이그레이션 스크립트 | ~150 |
| `supabase/migrations/005_entity_tagging.sql` | 스키마 변경 | ~30 |
| `backend/tests/test_title_extractor.py` | 추출기 테스트 | ~60 |
| `backend/tests/test_type_classifier.py` | 분류기 테스트 | ~60 |

### 10.2 Modified Files

| File | Changes |
|------|---------|
| `backend/app/core/rag/retriever.py` | `_filter_by_entities`, `_apply_entity_boost` 추가 |
| `backend/app/core/entity/__init__.py` | 새 모듈 export |

---

## Document Info

| Item | Value |
|------|-------|
| Version | 1.0 |
| Created | 2026-02-25 |
| Author | Claude (AI) |
| Phase | Design |
| Plan Reference | `docs/01-plan/features/entity-tagging-improvement.plan.md` |
| Next Step | `/pdca do entity-tagging-improvement` |
