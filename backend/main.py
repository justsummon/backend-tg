"""
Career Navigator — backend (FastAPI).

Эндпоинты:
  POST /profile   — сохранить профиль ученика, вернуть profile_id
  POST /analyze    — прогнать профиль через AI, сохранить и вернуть результат
  GET  /result/{result_id} — получить сохранённый результат по id
  GET  /result/by-telegram/{telegram_id} — последний результат пользователя
  GET  /health     — проверка живости сервиса

Запуск:
  uvicorn main:app --reload
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import database
from ai_engine import analyze_profile
from models import AnalyzeRequest, AnalyzeResponse, AnalysisResult, UserProfile

app = FastAPI(title="Career Navigator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # для хакатона ок; в проде — список конкретных доменов
    allow_methods=["*"],
    allow_headers=["*"],
)

database.init_db()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/profile")
def create_profile(profile: UserProfile):
    profile_id = database.save_profile(profile.telegram_id, profile.model_dump())
    return {"profile_id": profile_id}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    profile = request.profile
    profile_id = database.save_profile(profile.telegram_id, profile.model_dump())

    try:
        raw_result = analyze_profile(profile)
        result = AnalysisResult(**raw_result)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"AI не смог построить корректный ответ: {e}",
        )

    result_id = database.save_result(profile_id, result.model_dump())
    return AnalyzeResponse(result_id=result_id, result=result)


@app.get("/result/{result_id}")
def get_result(result_id: str):
    result = database.get_result(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Результат не найден")
    return result


@app.get("/result/by-telegram/{telegram_id}")
def get_result_by_telegram(telegram_id: int):
    result = database.get_latest_result_for_telegram_id(telegram_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Результатов пока нет")
    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
