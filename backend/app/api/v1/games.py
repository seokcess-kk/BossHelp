from fastapi import APIRouter, HTTPException
from app.db.models import GamesResponse, Game, PopularQuestionsResponse, PopularQuestion
from app.db.supabase import db

router = APIRouter()

# 인기 질문 Mock 데이터 (추후 DB 연동)
MOCK_POPULAR = {
    "elden-ring": [
        PopularQuestion(question="말레니아 어떻게 깸?", category="boss_guide", ask_count=150),
        PopularQuestion(question="출혈 빌드 추천해줘", category="build_guide", ask_count=120),
        PopularQuestion(question="라니 퀘스트 순서", category="npc_quest", ask_count=100),
    ],
    "sekiro": [
        PopularQuestion(question="겐이치로 어떻게 깸?", category="boss_guide", ask_count=80),
        PopularQuestion(question="튕겨내기 타이밍", category="mechanic_tip", ask_count=70),
    ],
}


@router.get("/games", response_model=GamesResponse)
async def get_games():
    """Get all available games from database."""
    games_data = await db.get_games(active_only=True)
    games = [
        Game(
            id=g["id"],
            title=g["title"],
            genre=g.get("genre", "soulslike"),
            thumbnail_url=g.get("thumbnail_url"),
            is_active=g.get("is_active", True),
        )
        for g in games_data
    ]
    return GamesResponse(games=games)


@router.get("/games/debug/raw")
async def get_games_debug():
    """Debug endpoint to see raw DB response."""
    games_data = await db.get_games(active_only=False)
    return {"count": len(games_data), "games": games_data}


@router.get("/games/{game_id}/popular", response_model=PopularQuestionsResponse)
async def get_popular_questions(game_id: str):
    """Get popular questions for a specific game."""
    # DB에서 게임 존재 여부 확인
    game = await db.get_game(game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")

    # TODO: Replace with actual DB call
    # questions = await db.get_popular_questions(game_id)
    questions = MOCK_POPULAR.get(game_id, [])
    return PopularQuestionsResponse(questions=questions)
