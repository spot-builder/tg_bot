from aiogram import Bot, Dispatcher, executor, types
import logging
import os
import datetime
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters import Text
import pymysql
from weather import get_weather_forecast_by_api
from classes import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")
storage = MemoryStorage()
bot = Bot(os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot=bot, storage=storage)


def auth(func):
    def wrapper(message):
        if message['from']['id'] != 521994538:
            return message.answer("Для получения информации о существующих командах введите /help")
        return func(message)

    return wrapper


try:
    connection = pymysql.connect(
        host="localhost",
        user="user",
        password="vjwpEZ5",
        database="bot_db",
        cursorclass=pymysql.cursors.DictCursor
    )
except Exception as ex:
    print("Connection failed...")
    print(ex)


@dp.message_handler(commands=["help", "start"])
async def help_info(message: types.Message):
    await message.answer("/weather - команда для получения текущей погоды\n"
                         "/spending - учет расходов\n"
                         "/moneybox - копилка")


@dp.message_handler(commands="admin")
@auth
async def admin_panel(message: types.Message):
    await AdminForm.message.set()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    keyboard.add("Информация по имени", "Блокировка пользователя", "Изменение инфорации", "Отмена")
    await message.answer("Добро пожаловать в административную панель", reply_markup=keyboard)


@dp.message_handler(lambda message: message.text == "Информация по имени", state=AdminForm.message)
async def admin_get_proccess(message: types.Message, state: FSMContext):
    await state.finish()
    await AdminGet.message.set()
    await AdminGet.next()
    await message.answer("Введите имя пользователя")


@dp.message_handler(state=AdminGet.name)
async def admin_get_finish(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    data = await state.get_data()
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM `messages` WHERE name='{data.get('name')}'")
        db_data = cursor.fetchall()
    if db_data:
        await message.answer(
            f"Логин: {db_data[0].get('name')}\n"
            f"Пароль: {db_data[0].get('password')}\n"
            f"Деньги: {db_data[0].get('money')}\n"
            f"ID: {db_data[0].get('id')}\n"
            f"Login: {db_data[0].get('login')}\n"
            f"Причины: {db_data[0].get('reasons')}")
    else:
        await message.answer("Введите корректное имя")
    await state.finish()


@dp.message_handler(state='*', commands=['cancel', "отмена"])
@dp.message_handler(Text(equals=['cancel', "отмена"], ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply('Отменено', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands="moneybox")
async def moneybox_start(message: types.Message):
    await MoneyBoxForm.message.set()
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    keyboard.add("Создание копилки", "Внесение денег", "Ваши копилки", "Отмена")
    await message.reply("Выберите одну из функций", reply_markup=keyboard)


@dp.message_handler(lambda msg: msg.text == "Ваши копилки", state=MoneyBoxForm.message)
async def moneyboxget_start(msg: types.Message, state: FSMContext):
    await state.finish()
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT current_money, budget, aim FROM `money_box` WHERE id={msg['from']['id']}")
        sql_box_data = cursor.fetchall()
        finish_message = ''
        for i in sql_box_data:
            finish_message += f"Цель: {i.get('aim')}\n" \
                              f"Желаемая сумма: {i.get('budget')}\n" \
                              f"Текущее количество денег: {i.get('current_money')}\n\n"
        await msg.answer(finish_message)


@dp.message_handler(lambda message: message.text == "Создание копилки", state=MoneyBoxForm.message)
async def moneybox_start(message: types.Message, state: FSMContext):
    await state.finish()
    await MoneyBoxSet.message.set()
    await MoneyBoxSet.next()
    await message.answer("Какова цель вашего накопления?")


@dp.message_handler(state=MoneyBoxSet.aim)
async def moneyBoxSetProccess(msg: types.Message, state: FSMContext):
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM `money_box` WHERE aim='{msg.text}' AND id={msg['from']['id']}")
        if cursor.fetchall():
            await msg.answer("Такая цель уже существует")
            await state.finish()
        else:
            await state.update_data(aim=msg.text)
            await msg.answer("Введите желаемую сумму")
            await MoneyBoxSet.next()


@dp.message_handler(state=MoneyBoxSet.desired_amount)
async def moneyboxsetend(msg: types.Message, state: FSMContext):
    await state.update_data(amount=msg.text)
    await msg.answer("Введите текущее количество денег")
    await MoneyBoxSet.next()


@dp.message_handler(state=MoneyBoxSet.current_money)
async def moneyboxset_info(msg: types.Message, state: FSMContext):
    await state.update_data(current=msg.text)
    data = await state.get_data()
    with connection.cursor() as cursor:
        cursor.execute(
            f"INSERT INTO `money_box` (id, current_money, budget, aim) VALUES({msg['from']['id']}, "
            f"{data['current']}, {data['amount']}, '{data['aim']}') ")
        connection.commit()
    await state.finish()
    await msg.answer("Запись сделана")


@dp.message_handler(commands='spending')
async def cmd_start(message: types.Message):
    await Form.message.set()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True)
    markup.add("Регистрация", "Получение информации", "Внесение информации", "Отмена")
    await message.reply("Выберите одну из функций", reply_markup=markup)


@dp.message_handler(lambda message: message.text == "Получение информации", state=Form.message)
async def cmd_get_process(msg: types.Message, state: FSMContext):
    await state.finish()
    await FormGet.message.set()
    await FormGet.next()
    await msg.answer("Введите имя")


@dp.message_handler(state=FormGet.name)
async def getting_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data_get:
        data_get['name'] = message.text
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM `messages` WHERE name='{data_get.get('name')}';")
        if not cursor.fetchall():
            await message.reply("Логин неверный")
            await state.finish()
        else:
            await FormGet.next()
            await message.reply("Введите пароль")


@dp.message_handler(state=FormGet.password)
async def getting_password(message: types.Message, state: FSMContext):
    async with state.proxy() as data_get:
        data_get['password'] = message.text
        with connection.cursor() as cursor:
            cursor.execute(
                f"SELECT * FROM `messages` WHERE name='{data_get.get('name')}' AND password='{data_get.get('password')}';")
            sql_data = cursor.fetchall()
            if not sql_data:
                await message.answer("Пароль неверный")
                await state.finish()
            else:
                await message.answer(f"Имя: {sql_data[0].get('name')}\n"
                                     f"Всего потрачено: {sql_data[0].get('money')} рубля/ей\n"
                                     f"Причины: {sql_data[0].get('reasons')}")
        await state.finish()


@dp.message_handler(lambda message: message.text == "Регистрация", state=Form.message)
async def cmd_set_process(msg: types.Message, state: FSMContext):
    await state.finish()
    await SignUp.message.set()
    await SignUp.next()
    await msg.answer("Введите имя")


@dp.message_handler(state=SignUp.name)
async def signup_name(message: types.Message, state: FSMContext):
    with connection.cursor() as cursor:
        cursor.execute("SELECT name FROM `messages`;")
        data = cursor.fetchall()
        names = []
        for i in data:
            names.append(i.get('name'))
        if message.text in names:
            await message.reply("Пользователь уже существует")
            await state.finish()
        else:
            await message.reply("Введите пароль")
            await state.update_data(name=message.text)
            await SignUp.next()


@dp.message_handler(state=SignUp.password)
async def signup_password(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if len(message.text) >= 6:
        with connection.cursor() as cursor:
            cursor.execute("INSERT INTO `messages` (name, password, id, login) VALUES" +
                           f"('{data['name']}', '{message.text}', '{message['from']['id']}', '{message['from']['username']}')")
            connection.commit()
        await message.answer("Регистрация прошла успешно")
    else:
        await message.answer("Длина пароля меньше 6 символов")
    await state.finish()


@dp.message_handler(lambda message: message.text == "Внесение информации", state=Form.message)
async def cmd_set_process(msg: types.Message, state: FSMContext):
    await state.finish()
    await FormSet.message.set()
    await FormSet.next()
    await msg.answer("Введите имя")


@dp.message_handler(state=FormSet.name)
async def setting_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    data_set = await state.get_data()
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT * FROM `messages` WHERE name='{data_set.get('name')}';")
        if not cursor.fetchall():
            await message.reply("Логин неверный")
            await state.finish()
        else:
            await message.reply("Введите пароль")
            await FormSet.next()


@dp.message_handler(state=FormSet.password)
async def setting_password(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    data_set = await state.get_data()
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT * FROM `messages` WHERE name='{data_set.get('name')}' AND password='{data_set.get('password')}';")
        sql_data = cursor.fetchall()
        if not sql_data:
            await message.reply("Пароль неверный")
            await state.finish()
        else:
            await FormSet.next()
            await state.update_data(current_money=sql_data[0].get('money'),
                                    current_message=sql_data[0].get('reasons'))
            await message.answer("Авторизация прошла успешно. Введите стоимость ваших затрат")


@dp.message_handler(state=FormSet.money)
async def setting_cost(message: types.Message, state: FSMContext):
    await state.update_data(money=message.text)
    temp = await state.get_data()
    try:
        money_data = float(temp.get('money'))
        with connection.cursor() as cursor:
            cursor.execute(
                f"UPDATE `messages` SET money={(temp.get('current_money') or 0) + money_data} WHERE name='{temp.get('name')}'")
        await message.answer("Введите причину вашей траты")
        await FormSet.next()
    except ValueError:
        await message.answer("Введите корректное число")
        await state.finish()


@dp.message_handler(state=FormSet.text)
async def setting_reason(message: types.Message, state: FSMContext):
    await state.update_data(reason=message.text)
    data_set = await state.get_data()
    with connection.cursor() as cursor:
        cursor.execute(
            f"UPDATE `messages` SET reasons='{data_set['current_message'] or ''}; {data_set['reason']};'"
            f"WHERE name='{data_set.get('name')}'")
        connection.commit()
    await message.answer("Запись сделана")
    await state.finish()


@dp.message_handler(state=Form.message)
async def wrong_command(message: types.Message, state: FSMContext):
    await message.answer("Введите корректную команду")
    await state.finish()


@dp.message_handler(commands="weather")
async def weather_start(message: types.Message):
    await Weather.waiting_for_weather.set()
    await message.reply("Введите город")


@dp.message_handler(state=Weather.waiting_for_weather)
async def process_weather_name(message: types.Message, state: FSMContext):
    await state.update_data(weather_city=message.text.lower())
    weather_data = await state.get_data()
    try:
        info_city = get_weather_forecast_by_api(weather_data.get("weather_city"))
        await message.answer(
            f"Температура: {info_city.get('fact').get('temp')} градуса/ов\n"
            f"Ощущается как: {info_city.get('fact').get('feels_like')} градуса/ов\n"
            f"Текущее время: {datetime.datetime.fromtimestamp(info_city.get('now'))}\n"
            f"Время получения прогноза: {datetime.datetime.fromtimestamp(info_city.get('forecast').get('date_ts'))}\n"
            f"Скорость ветра: {info_city.get('fact').get('wind_speed')} м/с\n"
            f"Влажность воздуха: {info_city.get('fact').get('humidity')}%\n",
            parse_mode=types.ParseMode.HTML)
    except AttributeError:
        await message.reply("Введите корректный город")
    finally:
        await state.finish()


@dp.message_handler()
async def wrong_commands(message: types.Message):
    await message.answer("Для получения информации о существующих командах введите /help")


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
