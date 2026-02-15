from fastapi import APIRouter, HTTPException
from app.db.models import GamesResponse, Game, PopularQuestionsResponse, PopularQuestion

router = APIRouter()

# Mock data for development
MOCK_GAMES = [
    Game(id="elden-ring", title="Elden Ring", genre="soulslike", is_active=True),
    Game(id="sekiro", title="Sekiro: Shadows Die Twice", genre="soulslike", is_active=True),
    Game(id="hollow-knight", title="Hollow Knight", genre="metroidvania", is_active=True),
    Game(id="silksong", title="Hollow Knight: Silksong", genre="metroidvania", is_active=True),
    Game(id="lies-of-p", title="Lies of P", genre="soulslike", is_active=True),
]

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
    """Get all available games."""
    # TODO: Replace with actual DB call
    # games = await db.get_games()
    return GamesResponse(games=MOCK_GAMES)


@router.get("/games/{game_id}/popular", response_model=PopularQuestionsResponse)
async def get_popular_questions(game_id: str):
    """Get popular questions for a specific game."""
    if game_id not in [g.id for g in MOCK_GAMES]:
        raise HTTPException(status_code=404, detail="Game not found")

    # TODO: Replace with actual DB call
    # questions = await db.get_popular_questions(game_id)
    questions = MOCK_POPULAR.get(game_id, [])
    return PopularQuestionsResponse(questions=questions)
