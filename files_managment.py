import os
import shutil
from contextlib import suppress
from typing import Optional

from logger import logger


def load_profiles(path="profiles"):
    """Читает файл с парами userprofile: telegramid. Возвращает список кортежей."""
    profiles = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if ":" in line:
                profile, telegram_id = line.strip().split(":", 1)
                profiles.append((profile.strip(), telegram_id.strip()))
    return profiles


def get_directories_list(username, links):
    directories = []
    for link in links:
        shortcode = link.split("/")[-2]
        directories.append(f"{username}-{shortcode}")
    return directories


def clean_and_check_user_dirs(username, expected_dirs, root="."):
    """
    Удаляет лишние директории username-*, которые не входят в expected_dirs.
    Возвращает список директорий из expected_dirs, которых нет на диске.
    """
    actual_dirs = [d for d in os.listdir(root)
                   if os.path.isdir(os.path.join(root, d)) and d.startswith(f"{username}-")]

    for d in actual_dirs:
        if d not in expected_dirs:
            full_path = os.path.join(root, d)
            try:
                shutil.rmtree(full_path)
                logger.info(f"🗑️ Удалена лишняя директория: {d}")
            except Exception as e:
                logger.info(f"❌ Не удалось удалить {d}: {e}")

    missing = []
    for d in expected_dirs:
        full_path = os.path.join(root, d)
        if not os.path.exists(full_path):
            shortcode = full_path.split(f"{username}-")[-1]
            missing.append(shortcode)

    return missing


def get_telegram_ids_by_username(username, filepath="profiles"):
    ids = set()
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split(":")
            if len(parts) == 2 and parts[0].strip() == username:
                ids.add(parts[1].strip())
    return list(ids)


def folder_has_files(username: str, link: str, base_dir: Optional[str] = '.') -> bool:
    """
    Проверяет наличие папки `f\"{username}-{link}\"` в `base_dir` и что в ней есть хотя бы один файл.
    Возвращает True, если папка существует и содержит хотя бы один файл (включая поддиректории).
    """
    folder_name = f"content/{username}-{link}"
    path = os.path.join(base_dir, folder_name)

    if not os.path.isdir(path):
        return False

    for _, _, files in os.walk(path):
        if files:  # если есть любые файлы
            return True

    return False

def del_dir(path):
    with suppress(FileNotFoundError):
        shutil.rmtree(path)
