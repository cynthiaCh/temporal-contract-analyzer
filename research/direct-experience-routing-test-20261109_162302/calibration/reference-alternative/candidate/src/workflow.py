from dataclasses import dataclass

class Feed:
    def __init__(self, env, key, token):
        self.env,self.key,self.token=env,key,token
        self.listeners={}
        self.serial=self.sequence=0
    def listen(self, callback):
        self.serial+=1
        self.listeners[self.serial]=callback
        return self.serial
    def detach(self, token):
        self.listeners.pop(token,None)
    def emit(self, kind, sequence):
        frame=dict(feed=self.token,kind=kind,seq=sequence,rows=[self.token+':'+kind+':'+str(sequence)])
        for token in list(self.listeners):
            if token in self.listeners:
                self.listeners[token](frame)
    def start(self, mode):
        if mode=='deferred': self.env.defer(lambda: self.emit('snapshot',0))
        else: self.emit('snapshot',0)
    def delta(self):
        self.sequence+=1
        self.emit('delta',self.sequence)

@dataclass
class Visit:
    feed: Feed
    active: bool=True
    stop: object=lambda: None

class Workspace:
    def __init__(self, env, key):
        self.env,self.key,self.current=env,key,None
    def hide(self):
        old,self.current=self.current,None
        if old:
            old.active=False
            old.stop()
    def select(self, feed, mode):
        self.hide()
        visit=Visit(feed)
        self.current=visit
        def decoded(frame):
            self.env.output("history",self.key,frame)
            if not (self.current is visit): return
            def painted(_):
                if self.current is not visit:
                    return
                self.env.output("count",self.key,frame)
            self.env.resolve('paint',self.key,frame).add_done_callback(lambda result: painted(result.result()))
        def deliver(frame):
            self.env.resolve('decode',feed.key,frame).add_done_callback(lambda result: decoded(result.result()))
        token=feed.listen(deliver)
        visit.stop=lambda: feed.detach(token)
        feed.start(mode)

def collect_metrics(env, key, feed):
    frames=[]
    feed.start("synchronous")
    token=feed.listen(frames.append)
    def finish():
        feed.delta()
        feed.detach(token)
        env.output('metrics',key,frames)
    env.defer(finish)
