import logging
import os
import shutil
from contextlib import suppress

logger = logging.getLogger(__name__)

def folder_has_files(directory) -> bool:
    if not os.path.isdir(directory):
        logger.info('Directory is empty')
        return False

    for _, _, files in os.walk(directory):
        logger.debug(files)
        if files:
            return True

    return False

def move_directory(source_dir, destination_dir):
    try:
        shutil.move(source_dir, destination_dir)
        logger.info(f"Folder moved from {source_dir} to {destination_dir}")
        return True
    except FileNotFoundError:
        logger.warning(f"Error: Folder {source_dir} not found.")
    except Exception as e:
        logger.error(f"Error: {e}")
    return False

def delete_directory(path):
    with suppress(FileNotFoundError):
        shutil.rmtree(path)
        logger.info(f'Директория {path} удалена')