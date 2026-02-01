from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from config import CONTAINERS


def main_kb(is_admin=False):
    kb = [
        [KeyboardButton(text="📦 Открыть контейнер"), KeyboardButton(text="🎒 Инвентарь")],
        [KeyboardButton(text="🎰 Рулетка"),KeyboardButton(text="👥 Рефералы")],
        [KeyboardButton(text="📊 Топ"), KeyboardButton(text="ℹ️ Профиль")]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="🔒 Админ-панель")])

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def cases_kb():
    buttons = []
    for k, v in CONTAINERS.items():
        buttons.append([InlineKeyboardButton(text=f"{v['name']} — {v['price']}💰", callback_data=f"buy:{k}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


inventory_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="💰 Продать всё", callback_data="sell_all")],
    [InlineKeyboardButton(text="❌ Закрыть", callback_data="close")]
])

admin_kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="➕ Выдать деньги"), KeyboardButton(text="➖ Забрать деньги")],
    [KeyboardButton(text="📣 Рассылка"), KeyboardButton(text="📊 Статистика")],
    [KeyboardButton(text="🔙 Назад")]
], resize_keyboard=True)

# КЛАВИАТУРЫ РУЛЕТКИ
roulette_main_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔴/⚫ Цвет (x2)", callback_data="r_type:color"),
     InlineKeyboardButton(text="🔢 Чет/Нечет (x2)", callback_data="r_type:parity")],
    [InlineKeyboardButton(text="1️⃣-3️⃣ Ряды (x3)", callback_data="r_type:row"),
     InlineKeyboardButton(text="0️⃣ Зеро (x36)", callback_data="r_bet:zero")],
    [InlineKeyboardButton(text="❌ Выход", callback_data="r_close")]
])

roulette_color_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔴 Красное", callback_data="r_bet:red"),
     InlineKeyboardButton(text="⚫ Черное", callback_data="r_bet:black")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="r_back")]
])

roulette_parity_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🔢 Четное", callback_data="r_bet:even"),
     InlineKeyboardButton(text="🔢 Нечетное", callback_data="r_bet:odd")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="r_back")]
])

roulette_row_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="1️⃣ Ряд 1 (1,4,7...)", callback_data="r_bet:row1")],
    [InlineKeyboardButton(text="2️⃣ Ряд 2 (2,5,8...)", callback_data="r_bet:row2")],
    [InlineKeyboardButton(text="3️⃣ Ряд 3 (3,6,9...)", callback_data="r_bet:row3")],
    [InlineKeyboardButton(text="🔙 Назад", callback_data="r_back")]
])