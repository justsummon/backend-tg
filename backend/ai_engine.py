import json
import os
import google.generativeai as genai
from models import UserProfile

AI_PROVIDER = os.getenv("AI_PROVIDER", "google")

SYSTEM_PROMPT = """Ты — карьерный навигатор для школьников 9-11 классов.
Твоя задача — предложить от 3 до 5 РАЗНЫХ гипотез профессий.
Поле "why" должно ссылаться на слова ученика.
Отвечай СТРОГО валидным JSON без markdown.

Формат ответа:
{
  "hypotheses": [
    {
      "profession": "...",
      "why": "...",
      "match_score": 80,
      "specializations": ["...", "..."],
      "skills_gap": [
        {"skill": "...", "have_level": 50, "need_level": 90, "how_to_improve": "..."}
      ],
      "universities": [
        {"name": "...", "country": "...", "program": "...", "budget_level": "medium", "requirements": "..."}
      ],
      "roadmap": [
        {"timeframe": "10 класс", "action": "...", "why": "..."}
      ]
    }
  ]
}
"""

def build_user_prompt(profile: UserProfile) -> str:
    return (
        f"Класс: {profile.grade}\n"
        f"Интересы: {profile.interests}\n"
        f"Предметы: {profile.favorite_subjects}\n"
        f"Навыки: {profile.current_skills}\n"
        f"Бюджет: {profile.budget_level or 'не указано'}\n"
    )

def _call_google(user_prompt: str) -> str:
    genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
    model = genai.GenerativeModel(
        model_name=os.getenv("GOOGLE_MODEL", "gemini-1.5-flash"),
        system_instruction=SYSTEM_PROMPT
    )
    
    # Отключаем фильтры безопасности, чтобы Google не блокировал ответы про профессии
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    response = model.generate_content(
        user_prompt,
        generation_config={"response_mime_type": "application/json"},
        safety_settings=safety_settings
    )
    
    if not response.text:
        raise Exception("AI вернул пустой ответ. Возможно, сработал фильтр.")
    return response.text

def analyze_profile(profile: UserProfile) -> dict:
    user_prompt = build_user_prompt(profile)

    if AI_PROVIDER == "google":
        raw = _call_google(user_prompt)
    else:
        # Заглушка для OpenAI/Anthropic, если они не настроены
        raise Exception("Провайдер AI не настроен")

    raw = raw.strip().replace("```json", "").replace("```", "")
    return json.loads(raw)