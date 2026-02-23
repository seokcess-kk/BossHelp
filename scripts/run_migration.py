#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Supabase 마이그레이션 실행 스크립트
"""

import os
import sys
from pathlib import Path

# Windows 콘솔 UTF-8 출력 설정
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend"))

from dotenv import load_dotenv
from supabase import create_client

# backend/.env 로드
load_dotenv(project_root / "backend" / ".env")


def run_migration(sql_file: str):
    """SQL 파일 실행"""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

    if not supabase_url or not supabase_key:
        print("[ERROR] SUPABASE_URL or SUPABASE_SERVICE_KEY is not set.")
        return False

    # SQL 파일 읽기
    sql_path = project_root / sql_file
    if not sql_path.exists():
        print(f"[ERROR] SQL file not found: {sql_path}")
        return False

    sql_content = sql_path.read_text(encoding="utf-8")
    print(f"[INFO] Migration file: {sql_file}")
    print(f"[SQL]\n{sql_content}\n")

    # Supabase 클라이언트 생성
    supabase = create_client(supabase_url, supabase_key)

    try:
        # games 테이블에 직접 upsert
        games_data = [
            {
                "id": "dark-souls",
                "title": "Dark Souls: Remastered",
                "genre": "soulslike",
                "subreddit": "r/darksouls",
                "wiki_base_url": "https://darksouls.wiki.fextralife.com",
                "is_active": True,
            },
            {
                "id": "dark-souls-2",
                "title": "Dark Souls II: SOTFS",
                "genre": "soulslike",
                "subreddit": "r/DarkSouls2",
                "wiki_base_url": "https://darksouls2.wiki.fextralife.com",
                "is_active": True,
            },
            {
                "id": "dark-souls-3",
                "title": "Dark Souls III",
                "genre": "soulslike",
                "subreddit": "r/darksouls3",
                "wiki_base_url": "https://darksouls3.wiki.fextralife.com",
                "is_active": True,
            },
        ]

        for game in games_data:
            result = supabase.table("games").upsert(game, on_conflict="id").execute()
            print(f"[OK] {game['title']} added/updated")

        return True

    except Exception as e:
        print(f"[ERROR] Migration failed: {e}")
        return False


def main():
    print("=" * 60)
    print("Supabase Migration Runner")
    print("=" * 60)

    # Dark Souls 마이그레이션 실행
    success = run_migration("supabase/migrations/003_add_dark_souls.sql")

    if success:
        print("\n[SUCCESS] Migration completed!")

        # 확인을 위해 게임 목록 조회
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase = create_client(supabase_url, supabase_key)

        result = supabase.table("games").select("id, title, genre").execute()
        print("\n[INFO] Current game list:")
        print("-" * 40)
        for game in result.data:
            print(f"  - {game['title']} ({game['id']})")
    else:
        print("\n[FAILED] Migration failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
