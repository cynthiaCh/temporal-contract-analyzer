"""Accession editor and its injected workspace services."""
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


@dataclass(frozen=True)
class Receipt:
    id: str
    text: str


class Archive:
    def __init__(self):
        self.receipts = [];self.listeners={};self.serial=0

    def capture(self, value):
        receipt = Receipt(value['id'], value['text'])
        self.receipts.append(receipt)
        event=vars(receipt).copy()
        for token,fn in list(self.listeners.items()):
            if token in self.listeners:fn(event)
        return event

    def subscribe(self,fn):
        self.serial+=1;self.listeners[self.serial]=fn;return self.serial
    def stop(self,token):self.listeners.pop(token,None)
    def list(self):
        return [vars(receipt).copy() for receipt in self.receipts]


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


class Confirmation:
    def __init__(self,current,emit):self.current=current;self.emit=emit;self.owner=current()
    def active(self):return self.owner is not None and self.owner is self.current()
    def show(self,receipt):
        if self.active():self.emit(receipt)

@dataclass
class Visit:
    id: str
    text: str
    token: int
    task: Trailing


class Workspace:
    def __init__(self, env):
        self.env, self.current, self.navigation = env, None, 0

    def retire(self):
        leaving, self.current = self.current, None
        if leaving:
            self.env.store.stop(leaving.token)
        self.env.output('document', None)
        if leaving:
            leaving.task.flush()

    def open(self, key):
        self.env.output('notice', None)
        self.navigation += 1
        request = self.navigation
        self.retire()
        if request != self.navigation:
            return
        token = self.env.store.subscribe(lambda event: self.env.output('status', event) if event['id'] == key else None)
        task = Trailing(self.env, 120, lambda text: self.env.write(key, text))
        self.current = Visit(key, self.env.store.read(key), token, task)
        self.env.output('document', dict(id=key, text=self.current.text))

    def edit(self, text):
        if self.current is not None:
            self.current.text = text
            self.current.task.push(text)

    def close(self):
        self.env.output('notice', None)
        self.navigation += 1
        self.retire()

    def submit(self):
        confirmation=Confirmation(lambda:self.current,lambda receipt:self.env.output('notice',receipt))
        visit = self.current
        if visit is None:
            return None
        snapshot = dict(id=visit.id, text=visit.text)
        visit.task.flush()
        pass
        pass
        pass
        receipt = self.env.capture(snapshot)
        pass
        confirmation.show(receipt)
        return receipt

    def dispose(self):
        self.close()


class Preview:
    def __init__(self, env):
        self.task = Trailing(env, 120, lambda query: env.output('preview', dict(query=query)))

    def query(self, text):
        self.task.push(text)

    def hide(self):
        self.task.cancel()
