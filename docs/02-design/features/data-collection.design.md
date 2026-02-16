# BossHelp Data Collection Design

## Overview

| Item | Value |
|------|-------|
| Feature | data-collection |
| Phase | Design |
| Created | 2026-02-15 |
| Plan Reference | docs/01-plan/features/data-collection.plan.md |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Collection Pipeline                   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Reddit Crawler│    │ Wiki Crawler  │    │ (Future)      │
│   (PRAW)      │    │(BeautifulSoup)│    │ YouTube, etc  │
└───────┬───────┘    └───────┬───────┘    └───────────────┘
        │                     │
        └──────────┬──────────┘
                   ▼
        ┌─────────────────────┐
        │   Raw Data Store    │
        │   (JSON/Memory)     │
        └──────────┬──────────┘
                   │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
┌────────┐   ┌──────────┐   ┌─────────┐
│Cleaner │ → │Classifier│ → │ Quality │
└────────┘   └──────────┘   └────┬────┘
                                 │
                   ┌─────────────┼─────────────┐
                   ▼             ▼             ▼
              ┌────────┐   ┌──────────┐   ┌────────┐
              │Chunker │ → │ Embedder │ → │ Store  │
              └────────┘   └──────────┘   └────┬───┘
                                               │
                                               ▼
                                    ┌─────────────────┐
                                    │    Supabase     │
                                    │ (knowledge_base)│
                                    └─────────────────┘
```

## Component Specifications

### 1. Reddit Crawler (crawler/crawlers/reddit.py)

#### Interface

```python
class RedditCrawler:
    def __init__(self, config: RedditConfig):
        """PRAW 클라이언트 초기화"""

    async def crawl_subreddit(
        self,
        subreddit: str,
        game_id: str,
        flairs: list[str],
        min_upvotes: int = 10,
        limit: int = 500,
        time_filter: str = "year"
    ) -> list[RawDocument]:
        """서브레딧에서 포스트 수집"""

    async def crawl_game(self, game_id: str) -> list[RawDocument]:
        """게임 설정 기반 크롤링"""
```

#### Data Model

```python
@dataclass
class RawDocument:
    id: str                    # 고유 ID
    game_id: str               # 게임 식별자
    source: str                # "reddit" | "wiki"
    source_url: str            # 원본 URL
    title: str                 # 제목
    content: str               # 본문
    author: str | None         # 작성자
    upvotes: int | None        # Reddit 추천수
    created_at: datetime       # 작성일
    metadata: dict             # 추가 메타데이터
```

#### Rate Limiting

```python
# 초당 1 요청 제한
REDDIT_DELAY = 1.0  # seconds

async def rate_limited_request(self):
    await asyncio.sleep(REDDIT_DELAY)
```

### 2. Wiki Crawler (crawler/crawlers/wiki.py)

#### Interface

```python
class WikiCrawler:
    def __init__(self):
        """BeautifulSoup 기반 크롤러 초기화"""

    async def crawl_page(self, url: str, game_id: str) -> RawDocument | None:
        """단일 페이지 크롤링"""

    async def crawl_category(
        self,
        base_url: str,
        game_id: str,
        category: str,
        max_pages: int = 100
    ) -> list[RawDocument]:
        """카테고리 페이지 크롤링"""

    async def crawl_game(self, game_id: str) -> list[RawDocument]:
        """게임 전체 위키 크롤링"""
```

#### Target Categories

| Game | Categories |
|------|------------|
| Elden Ring | Bosses, Weapons, Armor, Locations, Talismans |
| Sekiro | Bosses, Prosthetic_Tools, Skills, Locations |
| Hollow Knight | Bosses, Charms, Areas, Enemies |
| Lies of P | Bosses, Weapons, Legion_Arms, Locations |

### 3. Data Cleaner (crawler/processors/cleaner.py)

#### Processing Steps

```python
class DataCleaner:
    def clean(self, doc: RawDocument) -> CleanedDocument:
        """데이터 정제 파이프라인"""
        content = doc.content

        # 1. HTML 태그 제거
        content = self.remove_html_tags(content)

        # 2. 마크다운 정리
        content = self.clean_markdown(content)

        # 3. URL 처리
        content = self.process_urls(content)

        # 4. 특수문자 정규화
        content = self.normalize_special_chars(content)

        # 5. 공백 정리
        content = self.normalize_whitespace(content)

        return CleanedDocument(...)
```

#### Cleaning Rules

| Rule | Description |
|------|-------------|
| HTML 태그 | `<script>`, `<style>` 완전 제거, 나머지 태그만 제거 |
| 마크다운 | 링크는 텍스트만 유지, 이미지 alt 텍스트 유지 |
| URL | `[링크]` 또는 `(출처: url)` 형식으로 변환 |
| 공백 | 연속 공백/줄바꿈을 단일로 정규화 |

### 4. Content Classifier (crawler/processors/classifier.py)

#### Categories

```python
class ContentCategory(Enum):
    BOSS = "boss"           # 보스 공략
    ITEM = "item"           # 아이템/장비
    LOCATION = "location"   # 지역/맵
    BUILD = "build"         # 빌드/스탯
    GENERAL = "general"     # 일반 팁
```

#### Classification Logic

```python
class ContentClassifier:
    # 키워드 기반 분류
    KEYWORDS = {
        "boss": ["boss", "defeat", "kill", "strategy", "phase", "attack pattern"],
        "item": ["weapon", "armor", "talisman", "charm", "item", "equip"],
        "location": ["area", "location", "map", "path", "find", "where"],
        "build": ["build", "stats", "level", "attribute", "vigor", "strength"],
    }

    def classify(self, doc: CleanedDocument) -> ContentCategory:
        """키워드 매칭 기반 분류"""
        scores = self.calculate_keyword_scores(doc.content)
        return max(scores, key=scores.get)
```

### 5. Quality Filter (crawler/processors/quality.py)

#### Quality Metrics

```python
@dataclass
class QualityMetrics:
    length_score: float      # 길이 점수 (0-1)
    info_density: float      # 정보 밀도 (0-1)
    relevance_score: float   # 관련성 점수 (0-1)
    total_score: float       # 종합 점수 (0-1)
```

#### Scoring Logic

```python
class QualityFilter:
    MIN_LENGTH = 100         # 최소 문자 수
    MAX_LENGTH = 10000       # 최대 문자 수
    MIN_QUALITY_SCORE = 0.3  # 최소 품질 점수

    def calculate_length_score(self, content: str) -> float:
        """길이 기반 점수 (100-2000자 최적)"""
        length = len(content)
        if length < self.MIN_LENGTH:
            return 0.0
        elif length < 500:
            return length / 500
        elif length <= 2000:
            return 1.0
        else:
            return max(0.5, 1.0 - (length - 2000) / 8000)

    def calculate_info_density(self, content: str) -> float:
        """정보 밀도 (고유 단어 비율)"""
        words = content.lower().split()
        unique_ratio = len(set(words)) / len(words) if words else 0
        return min(1.0, unique_ratio * 1.5)
```

### 6. Text Chunker (crawler/processors/chunker.py)

#### Chunking Strategy

```python
class TextChunker:
    MAX_TOKENS = 500         # 청크당 최대 토큰
    OVERLAP_TOKENS = 100     # 오버랩 토큰

    def chunk(self, doc: CleanedDocument) -> list[Chunk]:
        """문서를 청크로 분할"""
        # 1. 토큰화
        tokens = self.tokenizer.encode(doc.content)

        # 2. 청크 분할
        chunks = []
        start = 0
        while start < len(tokens):
            end = min(start + self.MAX_TOKENS, len(tokens))
            chunk_tokens = tokens[start:end]

            chunks.append(Chunk(
                content=self.tokenizer.decode(chunk_tokens),
                chunk_index=len(chunks),
                total_chunks=None,  # 나중에 설정
                parent_id=doc.id,
            ))

            start = end - self.OVERLAP_TOKENS
            if start >= len(tokens):
                break

        # 청크 수 업데이트
        for chunk in chunks:
            chunk.total_chunks = len(chunks)

        return chunks
```

#### Chunk Data Model

```python
@dataclass
class Chunk:
    content: str             # 청크 내용
    chunk_index: int         # 청크 인덱스 (0부터)
    total_chunks: int        # 전체 청크 수
    parent_id: str           # 원본 문서 ID
    embedding: list[float] | None = None
```

### 7. Embedder (crawler/processors/embedder.py)

#### Embedding Configuration

```python
class Embedder:
    MODEL = "text-embedding-3-small"
    DIMENSIONS = 1536
    BATCH_SIZE = 100

    async def embed_batch(self, chunks: list[Chunk]) -> list[Chunk]:
        """배치 임베딩 생성"""
        texts = [chunk.content for chunk in chunks]

        response = await self.client.embeddings.create(
            model=self.MODEL,
            input=texts
        )

        for i, chunk in enumerate(chunks):
            chunk.embedding = response.data[i].embedding

        return chunks
```

#### Rate Limiting

```python
# OpenAI Rate Limits (text-embedding-3-small)
# - 3,000 RPM (requests per minute)
# - 1,000,000 TPM (tokens per minute)

BATCH_DELAY = 0.5  # seconds between batches
```

### 8. Data Store (crawler/store.py)

#### Storage Interface

```python
class SupabaseStore:
    async def upsert_chunk(self, chunk: ProcessedChunk) -> bool:
        """청크 저장 (중복 시 업데이트)"""

    async def upsert_batch(self, chunks: list[ProcessedChunk]) -> int:
        """배치 저장"""

    async def get_stats(self, game_id: str) -> dict:
        """게임별 통계 조회"""
```

#### Database Schema (knowledge_base)

```sql
-- 이미 존재하는 테이블
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id TEXT NOT NULL,
    category TEXT NOT NULL,
    content TEXT NOT NULL,
    source_url TEXT,
    source_type TEXT,  -- "reddit" | "wiki"
    embedding VECTOR(1536),
    metadata JSONB DEFAULT '{}',
    quality_score FLOAT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(source_url, content)  -- 중복 방지
);

-- 인덱스
CREATE INDEX idx_knowledge_game_category ON knowledge_base(game_id, category);
CREATE INDEX idx_knowledge_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops);
```

## Pipeline Orchestration

### Main Pipeline (crawler/pipeline.py)

```python
class DataPipeline:
    def __init__(self):
        self.reddit_crawler = RedditCrawler(get_reddit_config())
        self.wiki_crawler = WikiCrawler()
        self.cleaner = DataCleaner()
        self.classifier = ContentClassifier()
        self.quality_filter = QualityFilter()
        self.chunker = TextChunker()
        self.embedder = Embedder()
        self.store = SupabaseStore()

    async def run(self, game_id: str, sources: list[str] = ["reddit", "wiki"]):
        """전체 파이프라인 실행"""

        # 1. 데이터 수집
        raw_docs = []
        if "reddit" in sources:
            raw_docs.extend(await self.reddit_crawler.crawl_game(game_id))
        if "wiki" in sources:
            raw_docs.extend(await self.wiki_crawler.crawl_game(game_id))

        print(f"수집 완료: {len(raw_docs)}개 문서")

        # 2. 정제
        cleaned = [self.cleaner.clean(doc) for doc in raw_docs]

        # 3. 분류
        classified = [self.classifier.classify(doc) for doc in cleaned]

        # 4. 품질 필터링
        filtered = [doc for doc in classified
                   if self.quality_filter.filter(doc)]

        print(f"품질 필터 통과: {len(filtered)}개 문서")

        # 5. 청킹
        chunks = []
        for doc in filtered:
            chunks.extend(self.chunker.chunk(doc))

        print(f"청크 생성: {len(chunks)}개")

        # 6. 임베딩
        embedded = await self.embedder.embed_all(chunks)

        # 7. 저장
        saved = await self.store.upsert_batch(embedded)

        print(f"저장 완료: {saved}개 청크")

        return {
            "raw_docs": len(raw_docs),
            "filtered": len(filtered),
            "chunks": len(chunks),
            "saved": saved
        }
```

### CLI Interface

```python
# crawler/__main__.py
import asyncio
import argparse
from crawler.pipeline import DataPipeline

def main():
    parser = argparse.ArgumentParser(description="BossHelp Data Collector")
    parser.add_argument("game_id", help="Game ID (e.g., elden-ring)")
    parser.add_argument("--sources", nargs="+", default=["reddit", "wiki"])
    parser.add_argument("--limit", type=int, default=500)

    args = parser.parse_args()

    pipeline = DataPipeline()
    result = asyncio.run(pipeline.run(args.game_id, args.sources))

    print(f"\n=== 수집 결과 ===")
    print(f"원본 문서: {result['raw_docs']}")
    print(f"품질 통과: {result['filtered']}")
    print(f"청크 생성: {result['chunks']}")
    print(f"저장 완료: {result['saved']}")

if __name__ == "__main__":
    main()
```

## Environment Configuration

### Required Environment Variables

```bash
# crawler/.env
# Reddit API
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USER_AGENT=BossHelp/1.0 by /u/your_username

# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJhbG...

# OpenAI
OPENAI_API_KEY=sk-...
```

### Game Configurations

```python
# crawler/config.py
GAME_CONFIGS = {
    "elden-ring": GameConfig(
        id="elden-ring",
        subreddit="Eldenring",
        wiki_base_url="https://eldenring.wiki.fextralife.com",
        wiki_categories=["Bosses", "Weapons", "Armor", "Locations", "Talismans"],
        min_upvotes=10,
        flairs=["Guide", "Tips/Hints", "Help", "Strategy"],
    ),
    "sekiro": GameConfig(
        id="sekiro",
        subreddit="Sekiro",
        wiki_base_url="https://sekiroshadowsdietwice.wiki.fextralife.com",
        wiki_categories=["Bosses", "Prosthetic_Tools", "Skills", "Locations"],
        min_upvotes=10,
        flairs=["Guide", "Tips", "Help"],
    ),
    # ... 추가 게임
}
```

## Execution Plan

### Step 1: Reddit API 테스트

```bash
# 환경변수 설정 후
cd crawler
python -c "
from crawlers.reddit import RedditCrawler
from config import get_reddit_config

crawler = RedditCrawler(get_reddit_config())
posts = crawler.test_connection('Eldenring')
print(f'테스트 성공: {len(posts)}개 포스트')
"
```

### Step 2: 게임별 수집

```bash
# Elden Ring
python -m crawler elden-ring --sources reddit wiki

# Sekiro
python -m crawler sekiro --sources reddit wiki

# Hollow Knight
python -m crawler hollow-knight --sources reddit wiki

# Lies of P
python -m crawler lies-of-p --sources reddit wiki
```

### Step 3: 검증

```bash
# 수집 통계 확인
python -c "
from store import SupabaseStore
import asyncio

async def check():
    store = SupabaseStore()
    for game in ['elden-ring', 'sekiro', 'hollow-knight', 'lies-of-p']:
        stats = await store.get_stats(game)
        print(f'{game}: {stats}')

asyncio.run(check())
"
```

## Success Criteria

| Metric | Target |
|--------|--------|
| Reddit 포스트 수집 | 게임당 100+ |
| Wiki 페이지 수집 | 게임당 200+ |
| 품질 필터 통과율 | 70%+ |
| 임베딩 생성 | 5,000+ 청크 |
| 저장 성공률 | 99%+ |
| RAG 검색 정확도 | Top-5에 관련 결과 포함 |

## Error Handling

### Retry Strategy

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def fetch_with_retry(url: str) -> str:
    """재시도 로직이 포함된 요청"""
    ...
```

### Error Logging

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)
```

## Next Steps

1. Reddit API 키 발급 (https://www.reddit.com/prefs/apps)
2. 환경변수 설정 (crawler/.env)
3. `/pdca do data-collection` 실행하여 구현 시작
