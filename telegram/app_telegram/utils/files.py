import logging
import os
import shutil
from contextlib import suppress

logger = logging.getLogger(__name__)

def delete_directory(path):
    with suppress(FileNotFoundError):
        shutil.rmtree(path)
        logger.info(f'Директория {path} удалена')


def folder_has_files(directory) -> bool:
    if not os.path.isdir(directory):
        logger.info('Directory is empty')
        return False

    for _, _, files in os.walk(directory):
        logger.debug(files)
        if files:
            return True

    return False