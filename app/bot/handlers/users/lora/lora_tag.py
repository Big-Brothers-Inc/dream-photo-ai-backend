from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandObject, Command
from app.repository.lora_tag import LoraTagRepository
from app.repository.lora_tag_relation import LoraTagRelationRepository
from app.utils.permissions import has_admin_permission

lora_tag_router = Router()
repo = LoraTagRepository()


@lora_tag_router.message(Command("create_lora_tag"))
async def create_lora_tag(message: Message, command: CommandObject):
    if not has_admin_permission(message.from_user.id, "LORA"):
        return await message.answer("❌ У вас нет прав для создания тега.")

    tag_name = command.args.strip() if command.args else None

    if not tag_name:
        return await message.answer("❗ Укажите название тега: /create_lora_tag <code>tag_name</code>")

    # Проверка, существует ли уже такой тег
    existing = repo.find_by_name(tag_name)
    if existing:
        return await message.answer(f"⚠️ Тег с названием <b>{tag_name}</b> уже существует.", parse_mode="HTML")

    tag = repo.create({"name": tag_name})

    if tag:
        await message.answer(f"✅ Тег <b>{tag['name']}</b> успешно создан! (ID: <code>{tag['tag_id']}</code>)",
                             parse_mode="HTML")
    else:
        await message.answer("❌ Ошибка при создании тега. Попробуйте позже.")


@lora_tag_router.message(Command("delete_lora_tag"))
async def delete_lora_tag(message: Message, command: CommandObject):
    if not has_admin_permission(message.from_user.id, "CEO"):
        return await message.answer("❌ У вас нет прав для удаления тега.")

    tag_id_or_name = command.args.strip() if command.args else None

    if not tag_id_or_name:
        return await message.answer("❗ Укажите ID или название тега: /delete_lora_tag <code>id_or_name</code>")

    tag = None
    if tag_id_or_name.isdigit():
        tag = repo.get_by_id(int(tag_id_or_name))
    else:
        found = repo.find_by_name(tag_id_or_name)
        if found:
            tag = found[0]

    if not tag:
        return await message.answer(f"❌ Тег <b>{tag_id_or_name}</b> не найден.", parse_mode="HTML")

    # Проверка связей
    relations = relation_repo.get_loras_for_tag(tag["tag_id"])
    if relations:
        return await message.answer(
            f"⚠️ Невозможно удалить тег <b>{tag['name']}</b>, так как он связан с {len(relations)} LoRA.",
            parse_mode="HTML"
        )

    deleted = repo.delete(tag["tag_id"])
    if deleted:
        await message.answer(f"🗑 Тег <b>{tag['name']}</b> успешно удалён.", parse_mode="HTML")
    else:
        await message.answer(f"❌ Не удалось удалить тег <b>{tag['name']}</b>.", parse_mode="HTML")
