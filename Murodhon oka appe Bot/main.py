import asyncio
import datetime
import requests
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- 1. SOZLAMALAR ---
BOT_TOKEN = "8930856087:AAHMEnqG3A_csGtecQWgFyyWu_s8hWiNQFw"
CHANNEL_ID = -1004493987758
FIREBASE_PROJECT_ID = "olmastat-bot"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- KEYBOARDS ---
sort_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🍎 1-sort (Gala)"), KeyboardButton(text="🍏 2-sort (Fuji)")],
        [KeyboardButton(text="🍎 3-sort (Golden)")]
    ],
    resize_keyboard=True
)

main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Yangi sotuv kiritish")],
        [KeyboardButton(text="📊 Bugungi hisobotim")]
    ],
    resize_keyboard=True
)

# --- FIREBASE FUNKSIYALARI ---
def save_to_firebase(data):
    url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/sales"
    payload = {
        "fields": {
            "user_id": {"integerValue": str(data["user_id"])},
            "user_name": {"stringValue": data["user_name"]},
            "username": {"stringValue": data["username"]},
            "apple_sort": {"stringValue": data["apple_sort"]},
            "quantity": {"integerValue": str(data["quantity"])},
            "date": {"stringValue": data["date"]},
            "time": {"stringValue": data["time"]}
        }
    }
    requests.post(url, json=payload)

def get_today_sales_grouped(today_str):
    url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/sales"
    response = requests.get(url)
    
    total_s1, total_s2, total_s3 = 0, 0, 0
    # Structure: { "Murodjon": { "🍎 1-sort (Gala)": 300, "🍏 2-sort (Fuji)": 150 } }
    users_data = {}
    
    if response.status_code == 200:
        docs = response.json().get("documents", [])
        for doc in docs:
            fields = doc.get("fields", {})
            date = fields.get("date", {}).get("stringValue", "")
            
            if date == today_str:
                sort = fields.get("apple_sort", {}).get("stringValue", "")
                qty = int(fields.get("quantity", {}).get("integerValue", 0))
                user = fields.get("user_name", {}).get("stringValue", "Noma'lum")
                
                # Umumiy sortlar bo'yicha yig'ish
                if "1-sort" in sort: total_s1 += qty
                elif "2-sort" in sort: total_s2 += qty
                elif "3-sort" in sort: total_s3 += qty
                
                # Foydalanuvchi va sort bo'yicha guruhlash
                if user not in users_data:
                    users_data[user] = {}
                
                users_data[user][sort] = users_data[user].get(sort, 0) + qty
                
    return total_s1, total_s2, total_s3, users_data

# --- 2. FSM (HOLATLAR) ---
class TradeState(StatesGroup):
    choose_sort = State()
    enter_quantity = State()

# --- 3. BOT HANDLERLARI ---
@dp.message(CommandStart())
@dp.message(F.text == "➕ Yangi sotuv kiritish")
async def start_cmd(message: types.Message, state: FSMContext):
    await message.answer(
        f"Salom, {message.from_user.full_name}!\n\n"
        f"Qaysi olma navini sotdingiz? Quyidagilardan tanlang:",
        reply_markup=sort_keyboard
    )
    await state.set_state(TradeState.choose_sort)

@dp.message(TradeState.choose_sort)
async def process_sort(message: types.Message, state: FSMContext):
    if message.text not in ["🍎 1-sort (Gala)", "🍏 2-sort (Fuji)", "🍎 3-sort (Golden)"]:
        await message.answer("Iltimos, pastdagi tugmalardan birini tanlang!", reply_markup=sort_keyboard)
        return
    
    await state.update_data(apple_sort=message.text)
    await message.answer(
        f"Siz **{message.text}** tanladingiz.\n\nQancha sotildi (kg da faqat raqam kiriting)?",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    await state.set_state(TradeState.enter_quantity)

@dp.message(TradeState.enter_quantity)
async def process_qty(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiritasiz (Masalan: 150):")
        return
    
    quantity = int(message.text)
    user_data = await state.get_data()
    apple_sort = user_data.get("apple_sort")
    
    now = datetime.datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M")
    
    user_id = message.from_user.id
    user_name = message.from_user.full_name
    username = f"@{message.from_user.username}" if message.from_user.username else user_name
    
    sales_data = {
        "user_id": user_id,
        "user_name": user_name,
        "username": username,
        "apple_sort": apple_sort,
        "quantity": quantity,
        "date": today_str,
        "time": time_str
    }
    save_to_firebase(sales_data)
    
    await message.answer(
        f"✅ **Muvaffaqiyatli saqlandi!**\n\n"
        f"👤 Xodim: {user_name}\n"
        f"🍎 Sort: {apple_sort}\n"
        f"📦 Miqdor: {quantity} kg\n"
        f"⏰ Vaqt: {time_str}\n\n"
        f"Yana sotuv kiritish uchun pastdagi tugmani bosing 👇",
        reply_markup=main_menu_keyboard,
        parse_mode="Markdown"
    )
    await state.clear()

@dp.message(F.text == "📊 Bugungi hisobotim")
async def show_my_report(message: types.Message):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    s1, s2, s3, users_data = get_today_sales_grouped(today_str)
    
    user_name = message.from_user.full_name
    my_data = users_data.get(user_name, {})
    
    if not my_data:
        await message.answer("Siz bugun hali hech qanday sotuv kiritmadingiz.", reply_markup=main_menu_keyboard)
        return
        
    total_my_qty = sum(my_data.values())
    sort_lines = "\n".join([f"  ▫️ {sort_name}: {qty} kg" for sort_name, qty in my_data.items()])
    
    await message.answer(
        f"📊 **Sizning bugungi jami sotuvlaringiz:**\n\n"
        f"👤 **{user_name}**\n"
        f"{sort_lines}\n"
        f"___________________\n"
        f"📦 **Jami:** {total_my_qty} kg",
        reply_markup=main_menu_keyboard,
        parse_mode="Markdown"
    )

# --- 4. KANALGA KUNLIK HISOBOT TASHASH (SOAT 22:00) ---
async def send_daily_report():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    s1, s2, s3, users_data = get_today_sales_grouped(today_str)
    
    total_all = s1 + s2 + s3
    
    # Xodimlar bo'yicha chiroyli blok yaratish
    users_report_blocks = []
    if users_data:
        for user, sorts in users_data.items():
            user_total = sum(sorts.values())
            sort_details = "\n".join([f"  ▫️ {sort_name}: {qty} kg" for sort_name, qty in sorts.items()])
            block = f"👤 **{user}** (Jami: {user_total} kg):\n{sort_details}"
            users_report_blocks.append(block)
        
        users_text = "\n\n".join(users_report_blocks)
    else:
        users_text = "Bugun hech kim sotuv kiritmadi."
    
    report_text = (
        f"📊 **BUGUNGI KUNLIK UMUMIY SOTUV HISOBOTI**\n"
        f"📅 **Sana:** {today_str}\n"
        f"___________________________________\n\n"
        f"🍎 **1-sort (Gala):** {s1} kg\n"
        f"🍏 **2-sort (Fuji):** {s2} kg\n"
        f"🍎 **3-sort (Golden):** {s3} kg\n"
        f"___________________________________\n"
        f"📦 **JAMI KUNLIK SOTUV:** {total_all} kg\n\n"
        f"👨‍🌾 **XODIMLAR BO'YICHA TARTIBLANGAN SOTUVLAR:**\n\n"
        f"{users_text}"
    )
    
    try:
        await bot.send_message(chat_id=CHANNEL_ID, text=report_text, parse_mode="Markdown")
    except Exception as e:
        print(f"Kanalga yuborishda xatolik: {e}")

scheduler = AsyncIOScheduler()
scheduler.add_job(send_daily_report, 'cron', hour=22, minute=0)

async def main():
    scheduler.start()
    print("Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())