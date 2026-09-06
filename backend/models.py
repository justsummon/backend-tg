"""
Pydantic-схемы для Career Navigator.
Всё, что приходит от WebApp и уходит от AI, описано здесь —
это контракт между фронтендом, бэкендом и AI-движком.
"""
from pydantic import BaseModel, Field
from typing import Optional


class UserProfile(BaseModel):
    telegram_id: Optional[int] = None
    grade: int = Field(..., ge=9, le=11, description="9, 10 или 11 класс")
    interests: str = Field(..., description="Хобби, игры, увлечения")
    favorite_subjects: str = Field(..., description="Любимые школьные предметы")
    current_skills: str = Field(..., description="Что ученик уже умеет")
    values: Optional[str] = Field(
        None, description="Что важно: деньги, творчество, стабильность, помощь людям..."
    )
    budget_level: Optional[str] = Field(
        None, description="low / medium / high — бюджет на обучение"
    )
    country_pref: Optional[str] = Field(
        None, description="Предпочтение по стране / городу для вуза"
    )


class SkillGapItem(BaseModel):
    skill: str
    have_level: int = Field(..., ge=0, le=100)
    need_level: int = Field(..., ge=0, le=100)
    how_to_improve: str


class University(BaseModel):
    name: str
    country: str
    program: str
    budget_level: str  # low / medium / high
    requirements: str


class RoadmapStep(BaseModel):
    timeframe: str        # например "9 класс, до конца года"
    action: str
    why: str


class ProfessionHypothesis(BaseModel):
    profession: str
    why: str
    match_score: int = Field(..., ge=0, le=100)
    specializations: list[str]
    skills_gap: list[SkillGapItem]
    universities: list[University]
    roadmap: list[RoadmapStep]


class AnalysisResult(BaseModel):
    hypotheses: list[ProfessionHypothesis]


class AnalyzeRequest(BaseModel):
    profile: UserProfile


class AnalyzeResponse(BaseModel):
    result_id: str
    result: AnalysisResult
