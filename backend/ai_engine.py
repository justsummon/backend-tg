import json
import os
import google.generativeai as genai
from models import UserProfile

# Получаем настройки из Render
AI_PROVIDER = os.getenv("AI_PROVIDER", "google").lower()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

SYSTEM_PROMPT = """Ты — карьерный навигатор для школьников.
Отвечай СТРОГО валидным JSON.
Формат: {"hypotheses": [{"profession": "...", "why": "...", "match_score": 80, "specializations": [], "skills_gap": [], "universities": [], "roadmap": []}]}
"""

def analyze_profile(profile: UserProfile) -> dict:
    if not GOOGLE_API_KEY:
        raise Exception("GOOGLE_API_KEY не найден в настройках!")

    genai.configure(api_key=GOOGLE_API_KEY)
    model = genai.GenerativeModel('gemini-flash-latest')

    user_prompt = f"Класс: {profile.grade}, Интересы: {profile.interests}, Навыки: {profile.current_skills}"

    # Запрос к AI
    response = model.generate_content(
        user_prompt,
        generation_config={"response_mime_type": "application/json"},
        safety_settings=[
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]
    )

    # Очистка от лишних символов
    raw_text = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(raw_text)