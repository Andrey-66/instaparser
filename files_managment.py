import os
import shutil


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
                print(f"🗑️ Удалена лишняя директория: {d}")
            except Exception as e:
                print(f"❌ Не удалось удалить {d}: {e}")

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