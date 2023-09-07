import logging
from aiogram import Bot, Dispatcher, types, executor
from aiogram.dispatcher.filters import Command 
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import token

logging.basicConfig(level=logging.INFO)

bot = Bot(token=token)
dp = Dispatcher(bot, storage=MemoryStorage())

exchange_rates = {
    'USD': 85.72,
    'EUR': 100.00,
    'RUB': 1.15,
    'KZT': 0.20,
}

class CurrencyExchangeForm(StatesGroup):
    currency = State()
    amount = State()

@dp.message_handler(Command('start'))
async def cmd_start(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    buttons = [KeyboardButton(text) for text in ['USD', 'EUR', 'RUB', 'KZT', 'Отмена']]
    markup.add(*buttons)
    await message.reply("Выберите валюту, которую нужно поменять:", reply_markup=markup)
    await CurrencyExchangeForm.currency.set()

@dp.message_handler(lambda message: message.text not in ['USD', 'EUR', 'RUB', 'KZT'], state=CurrencyExchangeForm.currency)
async def process_currency_invalid(message: types.Message):
    markup = ReplyKeyboardRemove()
    await message.reply("Выберите валюту из предложенных кнопок.", reply_markup=markup)

@dp.message_handler(lambda message: not message.text.isdigit(), state=CurrencyExchangeForm.amount)
async def process_amount_invalid(message: types.Message):
    await message.reply("Сумма должна быть числом. Попробуйте ещё раз.")

@dp.message_handler(lambda message: message.text.isdigit(), state=CurrencyExchangeForm.amount)
async def process_amount(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        amount = float(message.text)
        if amount <= 0:
            await message.reply("Сумма должна быть положительным числом. Попробуйте ещё раз.")
            return

        data['amount'] = amount

        currency = data['currency']
        exchange_rate = exchange_rates.get(currency)

        if exchange_rate is not None:
            converted_amount = amount * exchange_rate
            await message.reply(f"{amount} {currency} = {converted_amount:.2f} KGS")
        else:
            await message.reply("Извините, не удалось получить курс валюты.")

    await state.finish()

@dp.message_handler(lambda message: message.text.lower() == 'отмена', state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    await message.reply('Отмена.', reply_markup=ReplyKeyboardRemove())
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
