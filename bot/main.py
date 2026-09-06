import asyncio
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# --- Крошечный сервер для обмана Render ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive")

def run_health_server():
    port = int(os.getenv("PORT", 8000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

# --- Логика бота ---
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")
BACKEND_URL = os.getenv("BACKEND_URL")

bot = Bot(token=TOKEN)
dp = Dispatcher()

def webapp_keyboard(telegram_id: int) -> InlineKeyboardMarkup:
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
        "Привет! Я Career Navigator 🧭\nНажми кнопку ниже, чтобы начать 👇",
        reply_markup=webapp_keyboard(message.from_user.id),
    )

@dp.message(Command("result"))
async def get_last_result(message: types.Message):
    telegram_id = message.from_user.id
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BACKEND_URL}/result/by-telegram/{telegram_id}", timeout=10)
        except:
            await message.answer("Ошибка связи с бэкендом.")
            return

    if resp.status_code == 404:
        await message.answer("Результатов пока нет. Пройди диагностику через кнопку меню.")
        return

    data = resp.json()
    hyp = data["hypotheses"][0]
    roadmap_lines = "\n".join(f"• {step['timeframe']}: {step['action']}" for step in hyp["roadmap"])
    text = (f"🎯 Твоя профессия: <b>{hyp['profession']}</b>\n\n{hyp['why']}\n\n🗺️ План:\n{roadmap_lines}")
    await message.answer(text, parse_mode="HTML")

async def main():
    # Запускаем "обманку" в отдельном потоке
    threading.Thread(target=run_health_server, daemon=True).start()
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())