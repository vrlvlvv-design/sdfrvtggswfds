import random
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery
import database as db
import keyboards as kb

router = Router()


class RouletteStates(StatesGroup):
    waiting_amount = State()


# Красные номера в рулетке
RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}


@router.message(F.text == "🎰 Рулетка")
async def start_roulette(message: types.Message):
    user = await db.get_user(message.from_user.id)
    await message.answer(
        f"🎰 <b>Европейская Рулетка</b>\n💰 Твой баланс: {user[2]} монет\n\nВыберите тип ставки:",
        reply_markup=kb.roulette_main_kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("r_type:"))
async def select_type(call: CallbackQuery):
    t = call.data.split(":")[1]
    if t == "color":
        await call.message.edit_text("Выберите цвет:", reply_markup=kb.roulette_color_kb)
    elif t == "parity":
        await call.message.edit_text("Четное или Нечетное?", reply_markup=kb.roulette_parity_kb)
    elif t == "row":
        await call.message.edit_text("Выберите ряд (колонну):", reply_markup=kb.roulette_row_kb)
    await call.answer()


@router.callback_query(F.data == "r_back")
async def back_roulette(call: CallbackQuery):
    user = await db.get_user(call.from_user.id)
    await call.message.edit_text(
        f"🎰 <b>Европейская Рулетка</b>\n💰 Твой баланс: {user[2]} монет\n\nВыберите тип ставки:",
        reply_markup=kb.roulette_main_kb,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "r_close")
async def close_roulette(call: CallbackQuery):
    await call.message.delete()


@router.callback_query(F.data.startswith("r_bet:"))
async def ask_amount(call: CallbackQuery, state: FSMContext):
    bet_choice = call.data.split(":")[1]

    # Красивое название для сообщения
    names = {
        "red": "🔴 Красное", "black": "⚫ Черное",
        "even": "🔢 Четное", "odd": "🔢 Нечетное",
        "row1": "1️⃣ Ряд 1", "row2": "2️⃣ Ряд 2", "row3": "3️⃣ Ряд 3",
        "zero": "0️⃣ Зеро"
    }
    name = names.get(bet_choice, bet_choice)

    await state.update_data(bet_choice=bet_choice)
    await call.message.answer(f"Вы ставите на: <b>{name}</b>\n✍️ Введите сумму ставки (или 'отмена'):",
                              parse_mode="HTML")
    await state.set_state(RouletteStates.waiting_amount)
    await call.answer()


@router.message(RouletteStates.waiting_amount)
async def process_bet(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена":
        await state.clear()
        await message.answer("❌ Ставка отменена.")
        return

    if not message.text.isdigit():
        await message.answer("❌ Введите целое число!")
        return

    amount = int(message.text)
    user = await db.get_user(message.from_user.id)

    if amount <= 0:
        await message.answer("❌ Сумма должна быть больше 0")
        return

    if user[2] < amount:
        await message.answer(f"❌ Недостаточно средств! У вас: {user[2]}")
        return

    # Списываем деньги
    await db.update_balance(message.from_user.id, -amount)

    # Вращаем рулетку
    data = await state.get_data()
    choice = data['bet_choice']
    winning_number = random.randint(0, 36)

    # Определяем атрибуты выпавшего числа
    is_red = winning_number in RED_NUMBERS
    is_black = winning_number not in RED_NUMBERS and winning_number != 0
    is_zero = winning_number == 0
    is_even = (winning_number % 2 == 0) and not is_zero
    is_odd = (winning_number % 2 != 0)

    # Цвет числа для вывода
    num_color = "🟢" if is_zero else ("🔴" if is_red else "⚫")

    win_amount = 0

    # Проверка выигрыша
    if choice == "red" and is_red:
        win_amount = amount * 2
    elif choice == "black" and is_black:
        win_amount = amount * 2
    elif choice == "even" and is_even:
        win_amount = amount * 2
    elif choice == "odd" and is_odd:
        win_amount = amount * 2
    elif choice == "zero" and is_zero:
        win_amount = amount * 36
    elif choice == "row1" and winning_number != 0 and winning_number % 3 == 1:
        win_amount = amount * 3
    elif choice == "row2" and winning_number != 0 and winning_number % 3 == 2:
        win_amount = amount * 3
    elif choice == "row3" and winning_number != 0 and winning_number % 3 == 0:
        win_amount = amount * 3

    result_text = f"🎰 Выпало: {num_color} <b>{winning_number}</b>\n"

    if win_amount > 0:
        await db.update_balance(message.from_user.id, win_amount)
        result_text += f"🎉 <b>ПОБЕДА!</b> Вы выиграли {win_amount} монет!"
    else:
        result_text += "😔 Вы проиграли..."

    await message.answer(result_text, parse_mode="HTML")
    await state.clear()