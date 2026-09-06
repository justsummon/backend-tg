import json
import os
import google.generativeai as genai
from models import UserProfile

# Теперь можно выбрать "google"
AI_PROVIDER = os.getenv("AI_PROVIDER", "google") 

SYSTEM_PROMPT = """Ты — карьерный навигатор для школьников 9-11 классов.
Твоя задача — предложить от 3 до 5 гипотез профессий в формате JSON.
... (весь остальной текст промпта из оригинального файла) ...
Отвечай СТРОГО валидным JSON без markdown-разметки.
"""

def build_user_prompt(profile: UserProfile) -> str:
    return (
        f"Класс: {profile.grade}\n"
        f"Интересы: {profile.interests}\n"
        f"Любимые предметы: {profile.favorite_subjects}\n"
        f"Текущие навыки: {profile.current_skills}\n"
        f"Ценности: {profile.values or 'не указано'}\n"
        f"Бюджет: {profile.budget_level or 'не указано'}\n"
        f"Страна: {profile.country_pref or 'не указано'}\n"
    )

def _call_google(user_prompt: str) -> str:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model_name = os.getenv("GOOGLE_MODEL", "gemini-1.5-flash")
    
    model = genai.GenerativeModel(
        model_name=model_name,
        system_instruction=SYSTEM_PROMPT
    )
    
    response = model.generate_content(
        user_prompt,
        generation_config={"response_mime_type": "application/json"}
    )
    return response.text

def analyze_profile(profile: UserProfile) -> dict:
    user_prompt = build_user_prompt(profile)

    if AI_PROVIDER == "google":
        raw = _call_google(user_prompt)
    elif AI_PROVIDER == "anthropic":
        from openai import OpenAI # заглушка для логики выше
        # ... тут старая логика Anthropic ...
        raw = "{}" # упростил для примера
    else:
        # ... тут старая логика OpenAI ...
        raw = "{}"

    # Очистка от мусора
    raw = raw.strip().replace("```json", "").replace("```", "")
    return json.loads(raw)