from aiogram.dispatcher.filters.state import State, StatesGroup


class UserState(StatesGroup):
    """Состояния пользователя в процессе взаимодействия с ботом"""
    
    # Состояние загрузки фотографий
    uploading_photos = State()
    
    # Состояние ожидания обучения модели
    waiting_training = State()
    
    # Состояние генерации изображений
    generating_image = State()
    
    # Состояние ожидания оплаты
    waiting_payment = State() 