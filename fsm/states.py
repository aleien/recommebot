from aiogram.fsm.state import StatesGroup, State


class ManualRecommend(StatesGroup):
    selecting_category = State()
    typing_link = State()
    typing_comment = State()


class RecommendState(StatesGroup):
    typing_link = State()