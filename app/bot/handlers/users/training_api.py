import os
import logging
import shutil
import tempfile
from typing import List
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv(override=True)

# Проверяем, нужно ли отключить проверку подключения к базе данных
DISABLE_DB_CHECK = os.getenv("DISABLE_DB_CHECK", "false").lower() == "true"
print(f"[training_api.py] DISABLE_DB_CHECK из окружения: {os.getenv('DISABLE_DB_CHECK')}")
print(f"[training_api.py] DISABLE_DB_CHECK после обработки: {DISABLE_DB_CHECK}")

# Импортируем репозитории для работы с базой данных
if not DISABLE_DB_CHECK:
    from app.repository.model_repository import ModelRepository
    from app.repository.user_repository import UserRepository

# Импортируем утилиты для обработки изображений и запуска обучения
from app.utils.training_utils import (
    ensure_upload_dir_exists,
    get_user_upload_path,
    clear_user_upload_dir,
    process_and_convert_images,
    create_zip_archive,
    upload_zip_to_cloud,
    start_replicate_training,
    check_training_status,
    process_training_completion
)

# Настраиваем логгер
logger = logging.getLogger(__name__)

# Создаем роутер API
router = APIRouter(prefix="/api/training", tags=["training"])


# Модель данных для запроса на обучение модели
class TrainingRequest(BaseModel):
    user_id: int
    username: str
    model_name: str
    trigger_word: str = "TOK_USR"


# Модель данных для проверки статуса обучения
class StatusCheckRequest(BaseModel):
    training_id: str
    user_id: int


# Создаем экземпляры репозиториев
if not DISABLE_DB_CHECK:
    model_repository = ModelRepository()
    user_repository = UserRepository()


@router.post("/upload-photos", status_code=status.HTTP_200_OK)
async def upload_photos(
        user_id: int = Form(...),
        username: str = Form(...),
        photos: List[UploadFile] = File(...),
):
    """
    Загружает фотографии пользователя для обучения модели.
    
    Args:
        user_id: ID пользователя
        username: Имя пользователя
        photos: Список загружаемых фотографий
    
    Returns:
        Информация о загруженных фотографиях
    """
    # Проверяем наличие пользователя в базе данных
    if not DISABLE_DB_CHECK:
        user = user_repository.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"Пользователь с ID {user_id} не найден")

    # Проверяем, существует ли базовая директория для загрузок
    if not ensure_upload_dir_exists():
        raise HTTPException(status_code=500, detail="Не удалось создать директорию для загрузок")

    # Очищаем директорию пользователя от старых файлов
    if not clear_user_upload_dir(username, user_id):
        logger.warning(f"Не удалось очистить директорию пользователя {username}")

    # Создаем временные файлы для загруженных фотографий
    temp_files = []
    try:
        for photo in photos:
            # Проверяем тип файла (только изображения)
            content_type = photo.content_type
            if not content_type or not content_type.startswith("image/"):
                raise HTTPException(
                    status_code=400,
                    detail=f"Файл {photo.filename} не является изображением. Тип: {content_type}"
                )

            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False) as temp:
                # Сохраняем содержимое загруженного файла
                shutil.copyfileobj(photo.file, temp)
                temp_files.append(temp.name)

        # Обрабатываем и конвертируем загруженные изображения
        user_path = get_user_upload_path(username, user_id)
        converted_paths = process_and_convert_images(username, user_id, temp_files)

        if not converted_paths:
            raise HTTPException(status_code=500, detail="Не удалось обработать загруженные изображения")

        return {
            "status": "success",
            "message": f"Загружено и обработано {len(converted_paths)} изображений",
            "user_id": user_id,
            "username": username,
            "image_count": len(converted_paths),
            "user_upload_dir": user_path
        }

    except Exception as e:
        logger.error(f"Ошибка при загрузке фотографий: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Удаляем временные файлы
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


@router.post("/start-training", status_code=status.HTTP_200_OK)
async def start_training(request: TrainingRequest):
    """
    Запускает обучение модели с загруженными фотографиями.
    
    Args:
        request: Запрос на обучение модели
    
    Returns:
        Информация о запущенном обучении
    """
    # Извлекаем параметры из запроса
    user_id = request.user_id
    username = request.username
    model_name = request.model_name
    trigger_word = request.trigger_word

    try:
        # Проверяем наличие пользователя в базе данных
        if not DISABLE_DB_CHECK:
            user = user_repository.get(user_id)
            if not user:
                raise HTTPException(status_code=404, detail=f"Пользователь с ID {user_id} не найден")

            # Проверяем достаточное количество токенов у пользователя
            if user.get("token_balance", 0) < 300:  # Стоимость обучения - 300 токенов
                raise HTTPException(
                    status_code=403,
                    detail="Недостаточно токенов для обучения модели. Требуется минимум 300 токенов."
                )

        # Проверяем наличие загруженных изображений
        user_path = get_user_upload_path(username, user_id)
        image_files = [f for f in os.listdir(user_path) if f.endswith('.jpg')]

        if not image_files:
            raise HTTPException(
                status_code=400,
                detail="Не найдено загруженных изображений. Сначала загрузите фотографии."
            )

        # Создаем полные пути к изображениям
        image_paths = [os.path.join(user_path, f) for f in image_files]

        # Создаем ZIP-архив с изображениями
        zip_path = create_zip_archive(username, user_id, image_paths)
        if not zip_path:
            raise HTTPException(status_code=500, detail="Не удалось создать ZIP-архив с изображениями")

        # В режиме отключенной базы данных имитируем ответы
        if DISABLE_DB_CHECK:
            # Генерируем фиктивный ID тренировки
            import uuid
            training_id = str(uuid.uuid4())
            model_id = 1

            return {
                "status": "success",
                "message": "Обучение модели успешно запущено",
                "model_id": model_id,
                "training_id": training_id,
                "model_name": model_name,
                "trigger_word": trigger_word,
                "user_id": user_id,
                "username": username,
                "tokens_spent": 300
            }

        # Загружаем ZIP-архив в облачное хранилище
        zip_url = upload_zip_to_cloud(zip_path)
        if not zip_url:
            raise HTTPException(status_code=500, detail="Не удалось загрузить ZIP-архив в облачное хранилище")

        # Запускаем обучение модели на Replicate
        training_info = start_replicate_training(username, user_id, zip_url, model_name, trigger_word)
        if not training_info or training_info.get("status") == "failed":
            error_msg = training_info.get("error", "Неизвестная ошибка") if training_info else "Неизвестная ошибка"
            raise HTTPException(status_code=500, detail=f"Не удалось запустить обучение модели: {error_msg}")

        # Сохраняем информацию о модели в базе данных
        model_data = {
            "user_id": user_id,
            "name": model_name,
            "trigger_word": trigger_word,
            "training_id": training_info["training_id"],
            "status": "training",
            "is_public": False,
            "model_type": "user"
        }

        model_id = model_repository.create(model_data)

        # Вычитаем токены у пользователя
        user_repository.update_token_balance(user_id, -300)

        return {
            "status": "success",
            "message": "Обучение модели успешно запущено",
            "model_id": model_id,
            "training_id": training_info["training_id"],
            "model_name": model_name,
            "trigger_word": trigger_word,
            "user_id": user_id,
            "username": username,
            "tokens_spent": 300
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Ошибка при запуске обучения модели: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-status", status_code=status.HTTP_200_OK)
async def check_training_status_endpoint(request: StatusCheckRequest):
    """
    Проверяет статус обучения модели и обновляет информацию в базе данных.
    
    Args:
        request: Запрос на проверку статуса обучения
    
    Returns:
        Информация о статусе обучения
    """
    try:
        # В режиме отключенной базы данных имитируем ответы
        if DISABLE_DB_CHECK:
            return {
                "status": "success",
                "model_status": "training",
                "training_status": "processing",
                "model_id": 1,
                "training_id": request.training_id,
                "model_name": "Test Model",
                "trigger_word": "TOK_USR",
                "model_url": None
            }

        # Получаем информацию о модели из базы данных
        model = model_repository.get_by_training_id(request.training_id)
        if not model:
            raise HTTPException(status_code=404, detail=f"Модель с training_id {request.training_id} не найдена")

        # Проверяем соответствие модели пользователю
        if model["user_id"] != request.user_id:
            raise HTTPException(status_code=403, detail="У вас нет доступа к этой модели")

        # Если модель уже в завершенном состоянии, просто возвращаем информацию
        if model["status"] in ["ready", "failed"]:
            return {
                "status": "success",
                "model_status": model["status"],
                "model_id": model["id"],
                "training_id": model["training_id"],
                "model_name": model["name"],
                "trigger_word": model["trigger_word"],
                "model_url": model.get("model_url", None)
            }

        # Проверяем статус обучения на Replicate
        training_status = check_training_status(request.training_id)

        # Если статус изменился, обновляем информацию в базе данных
        if training_status["status"] in ["succeeded", "failed", "canceled"]:
            new_status = "ready" if training_status["status"] == "succeeded" else "failed"

            # Если обучение успешно завершено, обрабатываем результаты
            if new_status == "ready":
                # Получаем информацию о модели из результатов обучения
                completion_info = process_training_completion(
                    request.training_id,
                    request.user_id,
                    model["username"] if "username" in model else "user",
                    model["name"],
                    model["trigger_word"]
                )

                # Обновляем информацию о модели в базе данных
                model_repository.update_training_info(
                    model["id"],
                    new_status,
                    completion_info.get("model_url", None)
                )
            else:
                # Если обучение завершилось с ошибкой, просто обновляем статус
                model_repository.update_status(model["id"], new_status)

            # Получаем обновленную информацию о модели
            model = model_repository.get_by_training_id(request.training_id)

        return {
            "status": "success",
            "model_status": model["status"],
            "training_status": training_status["status"],
            "model_id": model["id"],
            "training_id": model["training_id"],
            "model_name": model["name"],
            "trigger_word": model["trigger_word"],
            "model_url": model.get("model_url", None)
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Ошибка при проверке статуса обучения модели: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user-models/{user_id}", status_code=status.HTTP_200_OK)
async def get_user_models(user_id: int):
    """
    Получает список моделей пользователя.
    
    Args:
        user_id: ID пользователя
    
    Returns:
        Список моделей пользователя
    """
    try:
        # В режиме отключенной базы данных имитируем ответы
        if DISABLE_DB_CHECK:
            # Имитация списка моделей пользователя
            return {
                "status": "success",
                "models": [
                    {
                        "id": 1,
                        "user_id": user_id,
                        "name": "Test Model 1",
                        "trigger_word": "TOK_USR",
                        "status": "ready",
                        "model_url": "https://example.com/model1",
                        "created_at": "2023-03-15T10:00:00"
                    }
                ]
            }

        # Проверяем наличие пользователя в базе данных
        user = user_repository.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"Пользователь с ID {user_id} не найден")

        # Получаем список моделей пользователя
        models = model_repository.get_by_user_id(user_id)

        return {
            "status": "success",
            "models": models
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Ошибка при получении списка моделей пользователя: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Добавляем эндпоинт для получения информации о пользователе
@router.get("/users/{user_id}", status_code=status.HTTP_200_OK)
async def get_user(user_id: int):
    """
    Получает информацию о пользователе.
    
    Args:
        user_id: ID пользователя
    
    Returns:
        Информация о пользователе
    """
    try:
        # В режиме отключенной базы данных имитируем ответы
        if DISABLE_DB_CHECK:
            return {
                "status": "success",
                "user": {
                    "user_id": user_id,
                    "username": f"user_{user_id}",
                    "token_balance": 500,
                    "tokens_spent": 0,
                    "models_trained": 1,
                    "images_generated": 0
                }
            }

        # Получаем информацию о пользователе из базы данных
        user = user_repository.get(user_id)
        if not user:
            raise HTTPException(status_code=404, detail=f"Пользователь с ID {user_id} не найден")

        # Добавляем дополнительные поля для фронтенда
        user_data = {
            "user_id": user.get("user_id"),
            "username": user.get("username"),
            "token_balance": user.get("tokens_left", 0),
            "tokens_spent": user.get("tokens_spent", 0),
            "models_trained": user.get("models_trained", 0),
            "images_generated": user.get("images_generated", 0),
            "last_active": user.get("last_active"),
            "registration_complete": user.get("registration_complete", False)
        }

        logger.info(f"Получены данные пользователя {user_id}: {user_data}")

        return {
            "status": "success",
            "user": user_data
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Ошибка при получении информации о пользователе: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def setup_training_api(app):
    """
    Регистрирует API-эндпоинты для обучения моделей в приложении FastAPI.
    
    Args:
        app: Экземпляр приложения FastAPI
    """
    app.include_router(router)
