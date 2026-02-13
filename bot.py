import os
import shutil

from telegram import InputMediaPhoto, InputMediaVideo

from acces import restricted
from files_managment import del_dir
from insta_download import get_content
from logger import logger

PROFILES_FILE="profiles"

@restricted
async def subscribe(update, context):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Использование: /subscribe <username>")
        return

    username = context.args[0].strip()
    telegram_id = str(update.effective_user.id)

    exists = False
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() == f"{username}: {telegram_id}":
                    exists = True
                    break

    if exists:
        await update.message.reply_text(f"✅ Вы уже подписаны на {username}.")
    else:
        with open(PROFILES_FILE, "a", encoding="utf-8") as f:
            f.write(f"{username}: {telegram_id}\n")
        await update.message.reply_text(f"🎉 Подписка на {username} оформлена!")


@restricted
async def unsubscribe(update, context):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Использование: /unsubscribe <username>")
        return

    username = context.args[0].strip()
    telegram_id = str(update.effective_user.id)
    target_line = f"{username}: {telegram_id}"

    if not os.path.exists(PROFILES_FILE):
        await update.message.reply_text("🔍 Вы не были подписаны.")
        return

    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = [line for line in lines if line.strip() != target_line]

    if len(new_lines) == len(lines):
        await update.message.reply_text(f"ℹ️ Вы не подписаны на {username}.")
    else:
        with open(PROFILES_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        await update.message.reply_text(f"❎ Вы успешно отписались от {username}.")


@restricted
async def mysubscriptions(update, context):
    telegram_id = str(update.effective_user.id)

    if not os.path.exists(PROFILES_FILE):
        await update.message.reply_text("📭 У вас пока нет подписок.")
        return

    subscriptions = []
    with open(PROFILES_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if f": {telegram_id}" in line:
                username = line.split(":", 1)[0].strip()
                subscriptions.append(username)

    if subscriptions:
        text = "📌 Ваши подписки:\n" + "\n".join(f"• {u}" for u in subscriptions)
    else:
        text = "📭 У вас пока нет подписок."

    await update.message.reply_text(text)


@restricted
async def download(update, context):
    if len(context.args) != 1:
        await update.message.reply_text("❌ Использование: /download <url>")
        return
    url = context.args[0].strip()
    if not (url.startswith("https://www.instagram.com/p/") or
        url.startswith("https://www.instagram.com/reel/")):
            await update.message.reply_text("❌ Некорректная ссылка")
            return
    try:
        shortcode = url.split("/")[4]
        get_content(shortcode)
        await send_content(f'content/{shortcode}', update.effective_user.id, context.bot)
    except Exception as e:
        await update.message.reply_text("Что-то пошло не так")


async def send_content(dir, telegram_id, bot, delete=True):
    files = os.listdir(dir)
    jpg_files = sorted([f for f in files if f.lower().endswith(".jpg")])
    mp4_files = sorted([f for f in files if f.lower().endswith(".mp4")])
    txt_files = [f for f in files if f.lower().endswith(".txt")]

    caption = ""
    if txt_files:
        with open(os.path.join(dir, txt_files[0]), "r", encoding="utf-8") as f:
            caption = f.read().strip()

    media = []
    for f in jpg_files:
        media.append(InputMediaPhoto(open(os.path.join(dir, f), "rb")))
    for f in mp4_files:
        media.append(InputMediaVideo(open(os.path.join(dir, f), "rb")))

    if not media:
        await bot.send_message(chat_id=telegram_id, text="⚠️ Контент не найден.")
        del_dir(dir)
        return

    if len(media) == 1:
        m = media[0]
        if isinstance(m, InputMediaPhoto):
            await bot.send_photo(chat_id=telegram_id, photo=m.media, caption=caption, parse_mode="HTML")
            logger.debug('Отправлено 1 фото')
        else:
            await bot.send_video(chat_id=telegram_id, video=m.media, caption=caption, parse_mode="HTML")
            logger.debug('Отправлено 1 видео')
        m.media.close()
    elif len(media) <= 10:
        await bot.send_media_group(chat_id=telegram_id, media=media, caption=caption)
        logger.debug(f'Отправлено {len(media)} медиа')
    else:
        media = [tuple(media[i:i + 10]) for i in range(0, len(media), 10)]
        for m in media:
            await bot.send_media_group(chat_id=telegram_id, media=m, caption=caption)
            logger.debug(f'Отправлено {len(m)} медиа')
    if delete:
        try:
            if os.path.isdir(dir) and dir not in [".", "/"]:
                shutil.rmtree(dir)
        except Exception as e:
            logger.error(e)
