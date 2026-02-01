import asyncio
import logging
import random
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import *
import database as db
import keyboards as kb
import admin
import roulette


async def start_bot():
    await db.init_db()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    # Подключаем админку
    dp.include_router(admin.router)
    dp.include_router(roulette.router)

    # --- ХЕНДЛЕРЫ ПОЛЬЗОВАТЕЛЯ ---

    @dp.message(CommandStart())
    async def cmd_start(message: types.Message, command: CommandObject):
        uid = message.from_user.id
        username = message.from_user.username

        # Реферальная система
        referrer_id = None
        args = command.args
        if args and args.isdigit() and int(args) != uid:
            referrer_id = int(args)

        is_new = await db.add_user(uid, username, referrer_id, START_BALANCE)

        text = f"👋 Привет! Твой баланс: {START_BALANCE}💰"
        if is_new and referrer_id:
            await db.update_balance(referrer_id, REFERRAL_REWARD)
            # Уведомление владельцу ссылки
            try:
                name = f"@{username}" if username else f"ID {uid}"
                await bot.send_message(referrer_id, f"🔔 <b>Новый реферал!</b>\nИгрок {name}\n+{REFERRAL_REWARD}💰",
                                       parse_mode="HTML")
            except:
                pass

        await message.answer(text, reply_markup=kb.main_kb(uid == ADMIN_ID))

    @dp.message(F.text == "📦 Открыть контейнер")
    async def open_cases(message: types.Message):
        user = await db.get_user(message.from_user.id)
        await message.answer(f"💳 Баланс: <b>{user[2]:,}</b>💰", reply_markup=kb.cases_kb(), parse_mode="HTML")

    @dp.callback_query(F.data.startswith("buy:"))
    async def buy_case(callback: CallbackQuery):
        cid = callback.data.split(":")[1]
        cnt = CONTAINERS[cid]
        uid = callback.from_user.id
        user = await db.get_user(uid)

        if user[2] < cnt['price']:
            await callback.answer("❌ Не хватает денег!", show_alert=True)
            return

        await db.update_balance(uid, -cnt['price'])

        # Генерация лута
        loot_items = []
        total_price = 0
        items_count = random.randint(4, 5)
        start, end = cnt["range"]
        pool = ITEMS_DB[start:end] or ITEMS_DB[:5]

        msg = f"📦 <b>{cnt['name']}</b>\n\n"

        for _ in range(items_count):
            base_name, base_price = random.choice(pool)

            # Рандом качества
            m_keys = list(MODIFIERS.keys())
            m_weights = [MODIFIERS[k][1] for k in m_keys]
            mod = random.choices(m_keys, weights=m_weights, k=1)[0]
            mult = MODIFIERS[mod][0]

            final_price = int(base_price * mult)
            await db.add_item(uid, base_name, mod, final_price)
            total_price += final_price

            icon = "💩" if final_price < 20 else "✨"
            msg += f"{icon} {mod} {base_name} — {final_price}💰\n"

        profit = total_price - cnt['price']
        profit_str = f"✅ +{profit}" if profit >= 0 else f"🔻 {profit}"
        msg += f"\n💳 Итого: {total_price}💰\n{profit_str}"

        # Кнопка повтора
        builder = InlineKeyboardBuilder()
        builder.button(text=f"🔄 Еще раз ({cnt['price']})", callback_data=f"buy:{cid}")

        await callback.message.answer(msg, reply_markup=builder.as_markup(), parse_mode="HTML")
        await callback.answer()

    @dp.message(F.text == "🎒 Инвентарь")
    async def show_inv(message: types.Message):
        inv = await db.get_inventory(message.from_user.id)
        if not inv: return await message.answer("Пусто 🕸")

        total = sum(x[2] for x in inv)
        txt = f"🎒 <b>Инвентарь ({len(inv)} шт.)</b>\nВсего: {total:,}💰\n\n"
        for i in inv[-10:]:
            txt += f"• {i[1]} {i[0]} — {i[2]}\n"
        await message.answer(txt, reply_markup=kb.inventory_kb, parse_mode="HTML")

    @dp.callback_query(F.data == "sell_all")
    async def sell(call: CallbackQuery):
        s = await db.sell_all(call.from_user.id)
        if s: await call.message.answer(f"💰 Продано на {s} монет!")
        await call.answer()

    @dp.callback_query(F.data == "close")
    async def close(call: CallbackQuery):
        await call.message.delete()

    @dp.message(F.text == "📊 Топ")
    async def show_top(message: types.Message):
        top = await db.get_top()
        txt = "🏆 <b>ТОП БОГАЧЕЙ</b>\n"
        for i, u in enumerate(top, 1):
            name = f"@{u[1]}" if u[1] else f"ID {u[0]}"
            txt += f"{i}. {name} — {u[2]:,}💰\n"
        await message.answer(txt, parse_mode="HTML")

    @dp.message(F.text == "👥 Рефералы")
    async def show_refs(message: types.Message):
        cnt = await db.get_referrals_count(message.from_user.id)
        bot = await message.bot.get_me()
        link = f"https://t.me/{bot.username}?start={message.from_user.id}"
        await message.answer(f"👥 Приглашено: {cnt}\n🔗 {link}")

    @dp.message(F.text == "ℹ️ Профиль")
    async def profile(message: types.Message):
        u = await db.get_user(message.from_user.id)
        await message.answer(f"🆔: {u[0]}\n💰: {u[2]:,}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(start_bot())