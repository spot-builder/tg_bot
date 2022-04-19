from aiogram.dispatcher.filters.state import State, StatesGroup


class Weather(StatesGroup):
    waiting_for_weather = State()


class MoneyBoxForm(StatesGroup):
    message = State()


class MoneyBoxGet(StatesGroup):
    message = State()
    name = State()


class MoneyBoxSet(StatesGroup):
    message = State()
    aim = State()
    desired_amount = State()
    current_money = State()



class Form(StatesGroup):
    message = State()


class SignUp(StatesGroup):
    message = State()
    name = State()
    password = State()


class FormSet(StatesGroup):
    message = State()
    name = State()
    password = State()
    money = State()
    text = State()


class FormGet(StatesGroup):
    message = State()
    name = State()
    password = State()


class AdminForm(StatesGroup):
    message = State()


class AdminGet(StatesGroup):
    message = State()
    name = State()
