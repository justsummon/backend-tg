"""
Career Navigator — Telegram Bot (aiogram 3.x).

Роль бота — точка входа и "напоминалка". Вся логика диагностики
живёт в WebApp + backend. Бот:
  /start   — приветствие + кнопка открытия WebApp
  /result  — прислать последний сохранённый roadmap текстом
             (полезно, если ученик закрыл WebApp и хочет план в чате)
"""
import asyncio
import logging
import os

import httpx
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN", "ВАШ_ТГ_БОТ_ТОКЕН")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-frontend-url.vercel.app")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

bot = Bot(token=TOKEN)
dp = Dispatcher()


def webapp_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
    # Передаём telegram_id как query-параметр, чтобы WebApp могла
    # привязать результат анализа к конкретному пользователю бота.
    url_with_id = f"{WEBAPP_URL}?tg_id={telegram_id}"
    return InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text="🚀 Начать путь в профессию",
                web_app=WebAppInfo(url=url_with_id),
            )
        ]]
    )


@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Привет! Я Career Navigator 🧭\n\n"
        "Я не выдам тебе один готовый ответ вроде «тебе подходит маркетинг». "
        "Вместо этого мы вместе построим твой маршрут: "
        "интересы → профессия → специальность → навыки, которые стоит подтянуть "
        "→ вузы → пошаговый план.\n\n"
        "Нажми кнопку ниже, чтобы начать 👇",
        reply_markup=webapp_keyboard(message.from_user.id),
    )


@dp.message(Command("result"))
async def get_last_result(message: types.Message):
    telegram_id = message.from_user.id
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(
                f"{BACKEND_URL}/result/by-telegram/{telegram_id}", timeout=10
            )
        except httpx.RequestError:
            await message.answer("Backend сейчас недоступен, попробуй чуть позже.")
            return

    if resp.status_code == 404:
        await message.answer(
            "У тебя пока нет сохранённого результата. Нажми /start и пройди диагностику."
        )
        return

    data = resp.json()
    hyp = data["hypotheses"][0]  # показываем топ-гипотезу
    roadmap_lines = "\n".join(
        f"• {step['timeframe']}: {step['action']}" for step in hyp["roadmap"]
    )
    text = (
        f"🎯 Твоя топ-профессия: <b>{hyp['profession']}</b> "
        f"(совпадение {hyp['match_score']}%)\n\n"
        f"<i>{hyp['why']}</i>\n\n"
        f"🗺️ План действий:\n{roadmap_lines}\n\n"
        f"Полную версию с skills gap и вузами смотри в WebApp: /start"
    )
    await message.answer(text, parse_mode="HTML")


# На случай, если WebApp отправит данные боту через sendData() —
# сейчас не используется (WebApp ходит напрямую в backend), но оставлено
# как задел, если понадобится уведомление в чат при завершении диагностики.
@dp.message(F.web_app_data)
async def on_webapp_data(message: types.Message):
    await message.answer("Готово! Результат сохранён. Посмотреть его снова — /result")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
