from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID
from keyboards import admin_kb, main_kb
import database as db

router = Router()


class AdminStates(StatesGroup):
    give_money = State()
    take_money = State()
    broadcast = State()


@router.message(F.text == "🔒 Админ-панель")
async def admin_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("🛠 Админ-панель", reply_markup=admin_kb)


@router.message(F.text == "🔙 Назад")
async def back_menu(message: types.Message):
    await message.answer("Главное меню", reply_markup=main_kb(message.from_user.id == ADMIN_ID))


@router.message(F.text == "➕ Выдать деньги")
async def ask_give(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("Введите USERNAME и СУММУ через пробел (например: durov 1000)")
    await state.set_state(AdminStates.give_money)


@router.message(AdminStates.give_money)
async def process_give(message: types.Message, state: FSMContext):
    try:
        data = message.text.split()
        if len(data) != 2:
            await message.answer("❌ Формат: юзернейм сумма")
            return

        username_input = data[0].replace("@", "")
        amount = int(data[1])

        # Ищем ID по юзернейму
        user = await db.get_user_by_username(username_input)
        if not user:
            await message.answer(f"❌ Пользователь @{username_input} не найден в базе бота.")
            return

        uid = user[0]
        await db.update_balance(uid, amount)
        await message.answer(f"✅ Выдано {amount} пользователю @{username_input} (ID: {uid})")
        try:
            await message.bot.send_message(uid, f"💳 Администратор выдал вам {amount} монет!")
        except:
            pass

    except ValueError:
        await message.answer("❌ Сумма должна быть числом")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()


@router.message(F.text == "➖ Забрать деньги")
async def ask_take(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("Введите USERNAME и СУММУ через пробел")
    await state.set_state(AdminStates.take_money)


@router.message(AdminStates.take_money)
async def process_take(message: types.Message, state: FSMContext):
    try:
        data = message.text.split()
        if len(data) != 2:
            await message.answer("❌ Формат: юзернейм сумма")
            return

        username_input = data[0].replace("@", "")
        amount = int(data[1])

        # Ищем ID по юзернейму
        user = await db.get_user_by_username(username_input)
        if not user:
            await message.answer(f"❌ Пользователь @{username_input} не найден.")
            return

        uid = user[0]
        await db.update_balance(uid, -amount)
        await message.answer(f"✅ Забрано {amount} у пользователя @{username_input}")

    except ValueError:
        await message.answer("❌ Сумма должна быть числом")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()


@router.message(F.text == "📊 Статистика")
async def show_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    cnt, money = await db.get_stats()
    await message.answer(f"📊 <b>Статистика:</b>\n👥 Игроков: {cnt}\n💰 Всего денег: {money}", parse_mode="HTML")


@router.message(F.text == "📣 Рассылка")
async def ask_broadcast(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("Пришлите сообщение (текст/фото) для рассылки")
    await state.set_state(AdminStates.broadcast)


@router.message(AdminStates.broadcast)
async def process_broadcast(message: types.Message, state: FSMContext):
    users = await db.get_all_users()
    count = 0
    await message.answer(f"🚀 Начинаю рассылку на {len(users)} чел...")
    for (uid,) in users:
        try:
            await message.copy_to(uid)
            count += 1
        except:
            pass
    await message.answer(f"✅ Рассылка завершена. Доставлено: {count}")
    await state.clear()