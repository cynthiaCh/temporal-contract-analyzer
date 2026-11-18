from copy import deepcopy

from .config import LOCAL_CONFIG


class RecordEditor:
    def __init__(self, form, load_config):
        self._form = form
        self._load_config = load_config

    async def open(self, record):
        self._form.begin_registration()
        config = deepcopy(LOCAL_CONFIG)
        config["initial_values"] = {
            "parent_id": record["parent_id"],
            "parent_code": record["parent_code"],
            "parent_name": record["parent_name"],
        }
        self._form.apply_config(config)
