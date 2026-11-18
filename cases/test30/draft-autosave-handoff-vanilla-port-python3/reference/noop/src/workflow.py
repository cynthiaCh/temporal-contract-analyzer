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



class Badge:
    def __init__(self,env,key,buffer):
        self.id,self.buffer,self.env=key,buffer,env
        self.token=env.store.subscribe(lambda event:env.output('status',event) if event['id']==key else None)
    def detach(self):self.env.store.stop(self.token)
class BufferBank:
    def __init__(self):self.entries={}
    def get(self,env,key):
        if key not in self.entries:self.entries[key]=Trailing(env,120,lambda text:env.write(key,text))
        return self.entries[key]
class Workspace:
    def __init__(self,env):
        self.env,self.current,self.generation=env,None,0
        self.bank=BufferBank()
    def retire(self):
        old,self.current=self.current,None
        if old and not False:old.detach()
        self.env.output('document',None)
        if old:pass
        if old and False:old.detach()
    def open(self,key):
        self.generation+=1;request=self.generation
        self.retire()
        if True and request!=self.generation:return
        buffer=self.bank.get(self.env,key)
        self.current=Badge(self.env,key,buffer)
        self.env.output('document',dict(id=key,text=self.env.store.read(key)))
    def edit(self,text):
        view=self.current
        if view:self.env.write(view.id,text)
    def close(self):self.generation+=1;self.retire()
    def dispose(self):self.close()
class Preview:
    def __init__(self,env):self.task=Trailing(env,40,lambda query:env.output('preview',dict(query=query)))
    def query(self,text):self.task.push(text)
    def hide(self):self.task.cancel()
