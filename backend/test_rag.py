#!/usr/bin/env python3
"""RAG Pipeline 테스트 스크립트."""

import sys
sys.stdout.reconfigure(encoding="utf-8")

import asyncio
from dotenv import load_dotenv
load_dotenv()

from app.core.rag.pipeline import RAGPipeline

def test_rag():
    """Elden Ring RAG 테스트."""
    pipeline = RAGPipeline()

    test_cases = [
        ("elden-ring", "How do I beat Malenia?"),
        ("elden-ring", "How do I beat Radahn?"),
        ("elden-ring", "Where can I find the Moonveil katana?"),
        ("elden-ring", "말레니아 공략법 알려줘"),
    ]

    for game_id, question in test_cases:
        print(f"\n{'='*60}")
        print(f"Game: {game_id}")
        print(f"Question: {question}")
        print(f"{'='*60}")

        try:
            result = pipeline.run(
                game_id=game_id,
                question=question,
                spoiler_level="heavy"  # 전체 스포일러 허용
            )

            print(f"\n[Answer]")
            print(result.answer[:500] + "..." if len(result.answer) > 500 else result.answer)
            print(f"\n[Sources] {len(result.sources)} chunks used")
            print(f"[Latency] {result.latency_ms}ms")

        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()

        print()

if __name__ == "__main__":
    test_rag()
