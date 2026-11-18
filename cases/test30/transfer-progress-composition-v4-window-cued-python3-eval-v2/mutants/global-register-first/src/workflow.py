class PublicationWindow:
    def __init__(self):self.arrived=0;self.published=0
    def arrive(self):self.arrived+=1;return self.arrived
    def publish(self,order):
        if order<=self.published:return False
        self.published=order;return True
class Subscription:
    @staticmethod
    def attach(env,file,active,audit,view):
        if not file['feed']:return lambda:None
        def listener(packet):
            order=active()
            if order is None:return
            def deliver(frame):
                audit(frame);view(frame,order)
            value=env.call('decode',file['token'],packet,env.bind(deliver))
            if not value['deferred']:deliver(value['frame'])
        callback=env.bind(listener)
        subscription=env.call('listen',file['token'],callback)
        env.call('start',file['token'])
        return lambda:env.call('unlisten',file['token'],subscription)
# A session owns visits, while attempt closures own source and decode callbacks.
class Visit:
    def __init__(self, number, file):self.id=number;self.file=file;self.handle=None;self.window=PublicationWindow()
class Attempt:
    def __init__(self, env, file, number, active=lambda:1, audit=lambda f:None, view=lambda f,o:None):
        self.env=env;self.file=file;self.number=number;self.aborted=False;self.stop=lambda:None
        env.call('transport',file['token'],number)
        self.stop=Subscription.attach(env,file,lambda:None if self.aborted else active(),audit,view)
        if self.aborted:self.stop()
    def cancel(self):
        if self.aborted:return
        self.aborted=True;self.stop();self.env.call('cancel',self.file['token'],self.number)
class Session:
    def __init__(self,env):self.env=env;self.visit=None;self.serial=0;self.attempts=0;self.tasks=[];self.disposed=False
    def current(self,v):return self.visit is v
    def enqueue(self,v,kind):
        self.attempts+=1;n=self.attempts
        entry=dict(fileId=v.file['id'],attemptId=n,visitId=v.id,kind=kind)
        self.env.call('record',entry)
        window=v.window
        def audit(frame):self.env.call('recordProgress',dict(fileId=v.file['id'],attemptId=n,frame=frame))
        def view(frame,order):
            if self.current(v) and window.publish(order):self.env.call('showProgress',dict(fileId=v.file['id'],attemptId=n,frame=frame))
        h=Attempt(self.env,v.file,n,lambda:window.arrive() if self.current(v) else None,audit,view);self.tasks.append(h);return h
    def notice(self,v,h):
        self.env.call('showQueued',dict(fileId=v.file['id'],attemptId=h.number,visitId=v.id,status='queued'))
    def release(self,v):
        h=v.handle;v.handle=None
        if h:h.cancel()
    def select(self,file):
        if self.disposed:return None
        self.serial+=1;request=self.serial;old=self.visit;self.visit=None
        if old:self.release(old)
        if self.disposed or self.serial!=request:return None
        v=Visit(request,file);self.visit=v;h=self.enqueue(v,'select')
        if self.current(v):v.handle=h;self.notice(v,h)
        else:h.cancel()
        return h
    def retry(self):
        v=self.visit
        if not v or not v.handle or self.disposed:return None
        v.handle.cancel()
        accepted=v
        h=self.enqueue(accepted,'retry')
        if self.current(accepted):accepted.handle=h
        else:h.cancel()
        if self.current(accepted):self.notice(accepted,h)
        return h
    def hide(self):
        self.serial+=1;old=self.visit;self.visit=None
        if old:self.release(old)
    def dispose(self):
        if self.disposed:return
        self.disposed=True;self.hide()
        for h in self.tasks:h.cancel()
    def snapshot(self):
        v=self.visit
        return dict(visitId=v.id if v else None,fileId=v.file['id'] if v else None,attemptId=v.handle.number if v and v.handle else None,disposed=self.disposed,attempts=self.attempts)

class Telemetry:
    def __init__(self,env,file):
        def listener(packet):
            def deliver(frame):env.call('recordDelta',frame)
            value=env.call('decode',file['token'],packet,env.bind(deliver))
            if not value['deferred']:deliver(value['frame'])
        callback=env.bind(listener)
        subscription=env.call('listen',file['token'],callback)
        env.call('start',file['token'])
        self.stop=lambda:env.call('unlisten',file['token'],subscription)
