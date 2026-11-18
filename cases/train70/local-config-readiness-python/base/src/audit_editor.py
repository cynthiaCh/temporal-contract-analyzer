class AuditEditor:
    def __init__(self, form, load_config):
        self._form = form
        self._load_config = load_config

    async def open(self, record):
        self._form.begin_registration()
        config = await self._load_config("audit-form")
        await self._form.ready()
        self._form.apply_config(config)
        self._form.write({"audit_id": record["audit_id"]})

