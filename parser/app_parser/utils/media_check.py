import logging
import os
import subprocess

logger = logging.getLogger(__name__)


def has_audio_stream(path: str) -> bool:
    """Проверяет через ffprobe, есть ли в видеофайле аудиодорожка.

    Нужно, чтобы отлавливать битые/немые видео, которые сторонние
    сервисы (iqsaved и т.п.) иногда отдают без звука — такие файлы
    не должны считаться успешно скачанными.
    """
    try:
        result = subprocess.run(
            [
                'ffprobe', '-v', 'error',
                '-select_streams', 'a',
                '-show_entries', 'stream=index',
                '-of', 'csv=p=0',
                path,
            ],
            capture_output=True, text=True, timeout=30,
        )
        return bool(result.stdout.strip())
    except Exception as e:
        logger.warning(f"Не удалось проверить аудиодорожку в {path}: {e}")
        # Если ffprobe недоступен/упал — не блокируем скачивание из-за проверки
        return True


def ensure_faststart(path: str) -> bool:
    """Переносит moov-атом в начало файла (без перекодирования).

    Сторонние сайты-скачиватели часто отдают mp4 с moov-атомом в конце.
    Такие файлы iOS (в т.ч. плеер Telegram на iPhone) нередко отказывается
    проигрывать, пока не докачает файл целиком, тогда как на Android
    проблем обычно не возникает. Ремукс дешёвый — стрим просто
    копируется (-c copy), перекодирования нет.
    """
    tmp_path = path + ".faststart.tmp.mp4"
    try:
        result = subprocess.run(
            [
                'ffmpeg', '-y',
                '-i', path,
                '-c', 'copy',
                '-movflags', '+faststart',
                tmp_path,
            ],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0 or not os.path.exists(tmp_path):
            logger.warning(f"Не удалось сделать faststart-ремукс {path}: {result.stderr}")
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            return False
        os.replace(tmp_path, path)
        return True
    except Exception as e:
        logger.warning(f"Ошибка при faststart-ремуксе {path}: {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False


def folder_has_silent_video(folder: str) -> bool:
    """Проверяет, есть ли в папке хотя бы одно .mp4-видео без звука.

    Используется после успешного скачивания (независимо от метода), чтобы
    решить, нужно ли предупредить получателя — видео без звука не всегда
    баг: у ролика может не быть звука по задумке автора либо звук из
    медиатеки Instagram недоступен для скачивания.
    """
    try:
        for f in os.listdir(folder):
            if f.lower().endswith('.mp4'):
                if not has_audio_stream(os.path.join(folder, f)):
                    return True
    except FileNotFoundError:
        pass
    return False
