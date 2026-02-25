#!/usr/bin/env python3
"""데이터베이스에서 특정 키워드 검색."""

import sys
sys.stdout.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv()

import os
from supabase import create_client

supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

def search_chunks(keyword: str, game_id: str = "elden-ring", limit: int = 10):
    """chunks 테이블에서 키워드 검색."""
    print(f"\n{'='*60}")
    print(f"Searching: '{keyword}' in {game_id}")
    print(f"{'='*60}")

    # content에서 키워드 검색
    result = supabase.table("chunks").select(
        "id, title, content, source_url, category"
    ).eq(
        "game_id", game_id
    ).ilike(
        "content", f"%{keyword}%"
    ).limit(limit).execute()

    print(f"Found: {len(result.data)} chunks")

    for i, chunk in enumerate(result.data[:5], 1):
        print(f"\n[{i}] {chunk['title']}")
        print(f"    Category: {chunk['category']}")
        print(f"    URL: {chunk['source_url']}")
        # 키워드 주변 텍스트 표시
        content = chunk['content']
        idx = content.lower().find(keyword.lower())
        if idx >= 0:
            start = max(0, idx - 50)
            end = min(len(content), idx + len(keyword) + 100)
            snippet = content[start:end]
            print(f"    Snippet: ...{snippet}...")

    return result.data

def count_by_category(game_id: str):
    """게임별 카테고리 분포 확인."""
    print(f"\n{'='*60}")
    print(f"Category distribution for {game_id}")
    print(f"{'='*60}")

    result = supabase.rpc(
        "count_chunks_by_category",
        {"p_game_id": game_id}
    ).execute()

    if result.data:
        for row in result.data:
            print(f"  {row['category']}: {row['count']}")
    else:
        # fallback: 수동 카운트
        categories = ["boss_guide", "build_guide", "item_location", "mechanic_tip", "progression_route", "npc_quest", "secret_hidden"]
        for cat in categories:
            count = supabase.table("chunks").select(
                "id", count="exact"
            ).eq("game_id", game_id).eq("category", cat).execute()
            print(f"  {cat}: {count.count}")

if __name__ == "__main__":
    # Malenia 검색
    search_chunks("Malenia", "elden-ring")

    # Radahn 검색
    search_chunks("Radahn", "elden-ring")

    # Moonveil 검색
    search_chunks("Moonveil", "elden-ring")

    # 카테고리 분포
    count_by_category("elden-ring")
