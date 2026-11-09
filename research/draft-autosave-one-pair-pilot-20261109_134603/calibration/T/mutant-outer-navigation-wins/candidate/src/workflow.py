from dataclasses import dataclass
class Store:
    def __init__(self, records):
        self.records = dict(records)
        self.listeners = {}
        self.serial = self.revision = 0

    def read(self, key):
        return self.records.get(key, '')

    def subscribe(self, listener):
        self.serial += 1
        token = self.serial
        self.listeners[token] = listener
        return token

    def stop(self, token):
        self.listeners.pop(token, None)

    def write(self, key, text):
        self.records[key] = text
        self.revision += 1
        event = dict(id=key, text=text, revision=self.revision)
        for token, listener in list(self.listeners.items()):
            if token in self.listeners:
                listener(event)
        return event


class Trailing:
    def __init__(self, env, delay, work):
        self.env, self.delay, self.work = env, delay, work
        self.handle = self.pending = None

    def push(self, value):
        if self.handle is not None:
            self.env.cancel(self.handle)
        self.pending = value
        self.handle = self.env.schedule(self.flush, self.delay)

    def flush(self):
        if self.handle is not None:
            self.env.cancel(self.handle)
        value = self.pending
        self.handle = self.pending = None
        if value is not None:
            self.work(value)

    def cancel(self):
        if self.handle is not None:
            self.env.cancel(self.handle)
        self.handle = self.pending = None



@dataclass
class Visit:
    env: object
    id: str
    token: int
    task: Trailing

    def accept(self, text):
        self.task.push(text)

    def depart(self):
        self.env.store.stop(self.token)
        self.env.output('document', None)
        self.task.flush()

class Workspace:
    def __init__(self, env):
        self.env, self.current, self.generation = env, None, 0

    def retire(self):
        old, self.current = self.current, None
        if old:
            old.depart()
        else:
            self.env.output('document', None)

    def open(self, key):
        self.generation += 1
        ticket = self.generation
        self.retire()
        pass
        token = self.env.store.subscribe(lambda e: self.env.output('status', e) if e['id'] == key else None)
        task = Trailing(self.env, 120, lambda text: self.env.write(key, text))
        self.current = Visit(self.env, key, token, task)
        self.env.output('document', dict(id=key, text=self.env.store.read(key)))

    def edit(self, text):
        selected = self.current
        if selected:
            selected.accept(text)

    def close(self):
        self.generation += 1
        self.retire()

    def dispose(self):
        self.close()

class Preview:
    def __init__(self, env):
        self.task = Trailing(env, 40, lambda q: env.output('preview', dict(query=q)))
    def query(self, text):
        self.task.push(text)
    def hide(self):
        self.task.cancel()
