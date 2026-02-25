"""Entity Tags Migration Script.

기존 청크에 primary_entity, entity_type을 추가합니다.
Title 기반으로 주 엔티티를 추출하고 유형을 분류합니다.

Usage:
    # Dry-run (실제 업데이트 없이 시뮬레이션)
    python migrate_entity_tags.py --dry-run

    # 실제 마이그레이션
    python migrate_entity_tags.py

    # 특정 게임만
    python migrate_entity_tags.py --game-id elden-ring
"""

import os
import sys
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# backend 경로 추가
backend_path = os.path.join(os.path.dirname(__file__), "..", "backend")
sys.path.insert(0, backend_path)

# .env 파일 로드 (backend 디렉토리에서)
load_dotenv(os.path.join(backend_path, ".env"))

from app.core.entity.title_extractor import get_title_extractor
from app.core.entity.type_classifier import get_type_classifier
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def migrate_chunks(
    batch_size: int = 100,
    dry_run: bool = False,
    game_id: str | None = None,
) -> dict:
    """
    기존 청크에 primary_entity, entity_type 추가.

    Args:
        batch_size: 배치 처리 크기
        dry_run: True면 실제 업데이트 없이 시뮬레이션
        game_id: 특정 게임만 처리 (None이면 전체)

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
    query = (
        supabase.table("chunks")
        .select("id", count="exact")
        .eq("is_active", True)
    )
    if game_id:
        query = query.eq("game_id", game_id)

    count_result = query.execute()
    total_count = count_result.count or 0

    logger.info(f"Total chunks to migrate: {total_count}")
    if dry_run:
        logger.info("DRY-RUN MODE: No actual updates will be made")

    stats = {
        "total": total_count,
        "processed": 0,
        "success": 0,
        "no_entity": 0,
        "errors": 0,
        "type_distribution": {},
        "started_at": datetime.now().isoformat(),
    }

    # 배치 처리
    offset = 0
    while offset < total_count:
        # 배치 조회
        query = (
            supabase.table("chunks")
            .select("id", "title", "category", "game_id")
            .eq("is_active", True)
        )
        if game_id:
            query = query.eq("game_id", game_id)

        result = query.range(offset, offset + batch_size - 1).execute()

        if not result.data:
            break

        batch_updates = []

        for chunk in result.data:
            try:
                chunk_id = chunk["id"]
                title = chunk.get("title", "")
                category = chunk.get("category", "")

                # 엔티티 추출
                entity = extractor.extract(title)

                if entity:
                    # 유형 분류
                    entity_type = classifier.classify(entity.name, category)

                    batch_updates.append({
                        "id": chunk_id,
                        "primary_entity": entity.name,
                        "entity_type": entity_type.value,
                    })

                    stats["success"] += 1

                    # 유형 통계
                    type_name = entity_type.value
                    stats["type_distribution"][type_name] = (
                        stats["type_distribution"].get(type_name, 0) + 1
                    )
                else:
                    stats["no_entity"] += 1

                stats["processed"] += 1

            except Exception as e:
                logger.error(f"Error processing chunk {chunk.get('id')}: {e}")
                stats["errors"] += 1
                stats["processed"] += 1

        # 배치 업데이트
        if batch_updates and not dry_run:
            for update in batch_updates:
                try:
                    supabase.table("chunks").update({
                        "primary_entity": update["primary_entity"],
                        "entity_type": update["entity_type"],
                    }).eq("id", update["id"]).execute()
                except Exception as e:
                    logger.error(f"Update failed for {update['id']}: {e}")
                    stats["errors"] += 1
                    stats["success"] -= 1

        # 진행 상황 로깅
        progress = (stats["processed"] / total_count * 100) if total_count > 0 else 0
        logger.info(
            f"Progress: {stats['processed']}/{total_count} ({progress:.1f}%) - "
            f"Success: {stats['success']}, No entity: {stats['no_entity']}, Errors: {stats['errors']}"
        )

        offset += batch_size

    stats["completed_at"] = datetime.now().isoformat()
    return stats


def print_stats(stats: dict) -> None:
    """통계 출력."""
    print("\n" + "=" * 60)
    print("Migration Statistics")
    print("=" * 60)
    print(f"Total chunks:       {stats['total']}")
    print(f"Processed:          {stats['processed']}")
    print(f"Success:            {stats['success']}")
    print(f"No entity found:    {stats['no_entity']}")
    print(f"Errors:             {stats['errors']}")
    print(f"Started at:         {stats['started_at']}")
    print(f"Completed at:       {stats.get('completed_at', 'N/A')}")

    print("\nEntity Type Distribution:")
    print("-" * 40)
    for entity_type, count in sorted(
        stats["type_distribution"].items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        percentage = (count / stats["success"] * 100) if stats["success"] > 0 else 0
        print(f"  {entity_type:15} {count:6} ({percentage:5.1f}%)")

    print("=" * 60)


def main():
    """CLI 엔트리포인트."""
    parser = argparse.ArgumentParser(
        description="Migrate entity tags for existing chunks"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for processing (default: 100)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate migration without making changes",
    )
    parser.add_argument(
        "--game-id",
        type=str,
        default=None,
        help="Migrate only specific game (e.g., elden-ring)",
    )

    args = parser.parse_args()

    logger.info(f"Starting migration (dry_run={args.dry_run}, game_id={args.game_id})")

    stats = migrate_chunks(
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        game_id=args.game_id,
    )

    print_stats(stats)

    if args.dry_run:
        print("\n[DRY-RUN] No changes were made. Run without --dry-run to apply.")
    else:
        print("\n[COMPLETE] Migration finished successfully!")


if __name__ == "__main__":
    main()
