import logging
import os

from telegram import InputMediaPhoto, InputMediaVideo

from app_telegram.utils.files import delete_directory

logger = logging.getLogger(__name__)

async def send_content(directory, telegram_id, bot):
    files = os.listdir(directory)
    jpg_files = sorted([f for f in files if f.lower().endswith(".jpg")])
    mp4_files = sorted([f for f in files if f.lower().endswith(".mp4")])
    txt_files = [f for f in files if f.lower().endswith(".txt")]

    caption = ""
    separate_caption = ''
    if txt_files:
        with open(os.path.join(directory, txt_files[0]), "r", encoding="utf-8") as f:
            caption = f.read().strip()

    if len(caption) >= 1000:
        separate_caption = caption
        caption = ""

    media = []
    for f in jpg_files:
        media.append(InputMediaPhoto(open(os.path.join(directory, f), "rb")))
    for f in mp4_files:
        media.append(InputMediaVideo(open(os.path.join(directory, f), "rb")))

    if not media:
        # await bot.send_message(chat_id=telegram_id, text="⚠️ Контент не найден.")
        delete_directory(directory)
        return

    if len(media) == 1:
        m = media[0]
        if isinstance(m, InputMediaPhoto):
            await bot.send_photo(chat_id=telegram_id, photo=m.media, caption=caption, parse_mode="HTML")
            logger.info('Отправлено 1 фото')
        else:
            await bot.send_video(chat_id=telegram_id, video=m.media, caption=caption, parse_mode="HTML")
            logger.info('Отправлено 1 видео')
        # m.media.close()
    elif len(media) <= 10:
        await bot.send_media_group(chat_id=telegram_id, media=media, caption=caption)
        logger.info(f'Отправлено {len(media)} медиа')
    else:
        media = [tuple(media[i:i + 10]) for i in range(0, len(media), 10)]
        for m in media:
            await bot.send_media_group(chat_id=telegram_id, media=m, caption=caption)
            logger.info(f'Отправлено {len(m)} медиа')
    if separate_caption:
        for i in range(0, len(separate_caption), 4000):
            part = separate_caption[i:i + 4000]
            await bot.send_message(chat_id=telegram_id, text=part)
            logger.info(f'Отправил часть описания отдельно:\n{part}')
