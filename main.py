import asyncio, os, sqlite3, random
from datetime import datetime, timedelta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message, WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
TOKEN = "8665488674:AAHdxdDS92gY_8DWDvWEkWP9SVdiOWakLvM"
ADMIN_ID = 5012299174 
URL_APP = "https://iodebmo66.github.io/bot_in_python_my66/" 

app = FastAPI()
bot = Bot(token=TOKEN)
dp = Dispatcher()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

def get_db():
    # Путь для сохранения базы данных на Amvera
    conn = sqlite3.connect("/data/cats.db")
    return conn

def init_db():
    if not os.path.exists("/data"):
        os.makedirs("/data")
    conn = get_db(); cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS players 
                   (id INTEGER PRIMARY KEY, username TEXT, weight REAL DEFAULT 0, 
                    last_feed TEXT, is_admin INTEGER DEFAULT 0)''')
    cur.execute("INSERT OR IGNORE INTO players (id, username, is_admin) VALUES (?, ?, 1)", (ADMIN_ID, "eZZkA11"))
    conn.commit(); conn.close()

@dp.message(F.text.lower() == "!котик")
async def feed_in_chat(m: Message):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT weight, last_feed FROM players WHERE id = ?", (m.from_user.id,))
    row = cur.fetchone()
    
    now = datetime.now()
    if row and row[1] and datetime.fromisoformat(row[1]) + timedelta(hours=6) > now:
        wait_time = (datetime.fromisoformat(row[1]) + timedelta(hours=6)) - now
        await m.reply(f"❌ Кот еще сыт! Подожди {str(wait_time).split('.')[0]}.")
        return

    gain = round(random.uniform(0.1, 0.5), 2)
    new_weight = round((row[0] if row else 0) + gain, 2)
    
    cur.execute('''INSERT OR REPLACE INTO players (id, username, weight, last_feed, is_admin) 
                   VALUES (?, ?, ?, ?, (SELECT is_admin FROM players WHERE id = ?))''', 
                (m.from_user.id, m.from_user.username, new_weight, now.isoformat(), m.from_user.id))
    conn.commit(); conn.close()
    await m.reply(f"🍖 Ты покормил котика!\n📈 +{gain} кг.\n⚖️ Вес: {new_weight} кг.")

@dp.message(Command("start"))
async def start(m: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="Открыть Mini App 🐱", web_app=WebAppInfo(url=URL_APP))
    ]])
    await m.answer("Привет! Корми котика командой !котик или заходи в приложение:", reply_markup=kb)

@app.get("/data/{uid}")
async def get_data(uid: int):
    conn = get_db(); cur = conn.cursor()
    cur.execute("SELECT weight FROM players WHERE id = ?", (uid,))
    row = cur.fetchone(); conn.close()
    return {"w": row[0] if row else 0}

@app.on_event("startup")
async def startup():
    init_db()
    asyncio.create_task(dp.start_polling(bot))

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 80))
    uvicorn.run(app, host="0.0.0.0", port=port)
