from typing import Protocol


class FormPort(Protocol):
    def begin_registration(self):
        ...

    async def ready(self):
        ...

    def apply_config(self, config):
        ...

    def write(self, values):
        ...

