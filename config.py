import os
import re

from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr


DOTENV = os.path.join(os.path.dirname(__file__), '.env')


class Environment(Enum):
    LOCAL = 0
    PRODUCTION = 1

    def is_local(self) -> bool:
        return self.value == Environment.LOCAL.value

    def is_prod(self) -> bool:
        return self.value == Environment.PRODUCTION.value


class Settings(BaseSettings):
    bot_token: SecretStr
    env: str

    # Начиная со второй версии pydantic, настройки класса настроек задаются
    # через model_config
    # В данном случае будет использоваться файла .env, который будет прочитан
    # с кодировкой UTF-8
    model_config = SettingsConfigDict(env_file=DOTENV, env_file_encoding='utf-8')


# При импорте файла сразу создастся
# и провалидируется объект конфига,
# который можно далее импортировать из разных мест
config = Settings()
environment_config = Environment.PRODUCTION
if config.env == 'local':
    environment_config = Environment.LOCAL

RECEPIES = 'Рецепты'
GIFTS = 'Подарки детям'
HOTEL = 'Отели/отдых'
CARE = 'Уход'
STUDY = 'Обучение'
SERVICES = 'Услуги'
NANNY = 'Няни'
ADVICE = 'Советы'
OTHER = 'Другое'
FURNITURE = 'Мебель'
DEVICES = 'Девайсы'
MEDS = 'Лекарства/добавки'
CLOTHES = 'Одежда'
TOYS = 'Игрушки'
FOOD = 'Продукты/питание'
DOC = 'Врачи и клиники'

CATEGORIES = [
    DOC, TOYS, CLOTHES, MEDS, DEVICES,
    FURNITURE, OTHER, ADVICE, NANNY, SERVICES,
    STUDY, CARE, HOTEL, GIFTS, RECEPIES, FOOD
]

category_keywords = {
    DOC: ['педиатр', 'врач', 'клиника', 'невролог', 'ортопед', 'логопед', 'дерматолог', 'стоматолог', 'хирург',
          'консультация', 'медцентр', 'анализы', 'массажист', 'обследование', 'лечение'],
    TOYS: ['игрушка', 'развивашки', 'монтессори', 'конструктор', 'пазлы', 'настольные игры', 'кубики', 'книжки',
           'куклы', 'машинки', 'погремушки', 'бизиборд'],
    CLOTHES: ['одежда', 'комбинезон', 'бодик', 'боди', 'шапка', 'штаны', 'куртка', 'костюм', 'носки', 'обувь',
              'слюнявчик', 'варежки'],
    MEDS: ['лекарство', 'сироп', 'витамины', 'добавки', 'ибупрофен', 'нурофен', 'капли', 'мазь', 'гель', 'пробиотики',
           'жаропонижающее', 'спрей'],
    DEVICES: ['термометр', 'увлажнитель', 'стерилизатор', 'радионяня', 'видеоняня', 'подогреватель', 'молокоотсос',
              'блендер', 'весы', 'трекер сна', 'очиститель воздуха'],
    FURNITURE: ['кроватка', 'стол', 'стульчик', 'манеж', 'комод', 'пеленальный столик', 'кресло', 'шкаф', 'матрас'],
    ADVICE: ['совет', 'рекомендация', 'делюсь опытом', 'подсказка', 'лайфхак', 'мой опыт', 'личный опыт'],
    NANNY: ['няня', 'гувернантка', 'бебиситтер', 'нянечка', 'помощница'],
    SERVICES: ['фотограф', 'репетитор', 'массаж', 'консультация', 'курсы', 'тренер', 'студия развития',
               'логопедические занятия', 'развивающие занятия'],
    STUDY: ['курс', 'школа', 'занятия', 'обучение', 'вебинар', 'тренинг', 'программа', 'мастер-класс'],
    CARE: ['подгузники', 'крем', 'влажные салфетки', 'шампунь', 'гель для купания', 'присыпка', 'средства ухода',
           'уход за кожей', 'купание'],
    HOTEL: ['отель', 'гостиница', 'отдых', 'поездка', 'путешествие', 'санаторий', 'курорт', 'отпуск', 'бронирование',
            'резорт'],
    GIFTS: ['подарок', 'презент', 'сувенир', 'сюрприз', 'набор', 'игрушечный подарок', 'сертификат на подарок'],
    RECEPIES: ['рецепт'],
    FOOD: ['банка', 'состав', 'перекус'],
}

link_pattern = re.compile(r'https?://\S+')
phone_pattern = re.compile(r'(\+7|8)\s?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}')

recommendation_prefixes = ['рекоменд', 'порекоменд', 'посовет', 'советую', 'помог', 'делюсь', 'понравил' ]
recommendation_str = '|'.join(recommendation_prefixes)
recommendation_regexp = f'(\s|\A)({recommendation_str}).*'
