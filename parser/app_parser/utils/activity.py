import json
import logging
import os
import sys
import time
from pathlib import Path

STATUS_FILE = Path("/content/.parser_status.json")
logger = logging.getLogger(__name__)
checked_profiles = set()


def set_activity(state, **details):
    temporary = STATUS_FILE.with_suffix(".tmp")
    try:
        activity = {"state": state, "checked_profiles": sorted(checked_profiles), **details}
        temporary.write_text(json.dumps(activity), encoding="utf-8")
        os.replace(temporary, STATUS_FILE)
    except OSError as error:
        logger.warning("Could not publish parser activity: %s", error)


if __name__ == "__main__":
    set_activity("sleeping", until=time.time() + int(sys.argv[1]))
