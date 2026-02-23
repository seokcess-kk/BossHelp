#!/usr/bin/env python3
"""
Dark Souls 시리즈 초기 데이터 수집 스크립트

사용법:
    cd crawler
    python crawl_dark_souls.py

필요 환경변수:
    - REDDIT_CLIENT_ID
    - REDDIT_CLIENT_SECRET
    - SUPABASE_URL
    - SUPABASE_SERVICE_KEY
    - OPENAI_API_KEY
"""

from pipeline import DataPipeline
from models import SourceType


def main():
    print("=" * 60)
    print("Dark Souls 시리즈 초기 데이터 수집 시작")
    print("=" * 60)

    # 수집할 게임 목록
    dark_souls_games = ["dark-souls", "dark-souls-2", "dark-souls-3"]

    pipeline = DataPipeline()

    results = pipeline.run_initial(
        game_ids=dark_souls_games,
        sources=[SourceType.REDDIT, SourceType.WIKI],
        reddit_limit=500,  # 게임당 Reddit 500개
        wiki_limit_per_category=50,  # 카테고리당 Wiki 50개
    )

    # 결과 출력
    print("\n" + "=" * 60)
    print("수집 결과")
    print("=" * 60)

    total_chunks = 0
    for key, result in results.items():
        status_icon = "✅" if result.status == "success" else "❌"
        print(f"{status_icon} {key}:")
        print(f"   - 페이지 수집: {result.pages_crawled}")
        print(f"   - 청크 생성: {result.chunks_created}")
        if result.error_message:
            print(f"   - 오류: {result.error_message}")
        total_chunks += result.chunks_created

    print(f"\n총 청크: {total_chunks}개")
    print("=" * 60)


if __name__ == "__main__":
    main()
