from dataclasses import dataclass
class Channel:
    def __init__(self,env,key,name):
        self.env,self.key,self.name=env,key,name
        self.listeners={};self.serial=0
    def listen(self,callback):
        self.serial+=1;self.listeners[self.serial]=callback;return self.serial
    def detach(self,token):
        self.listeners.pop(token,None)
    def emit(self,kind):
        value=self.name+':'+kind
        for token in list(self.listeners):
            if token in self.listeners:self.listeners[token](value)
    def connect(self,mode):
        if mode=='deferred':self.env.defer(lambda:self.emit('bootstrap'))
        else:self.emit('bootstrap')
    def update(self):self.emit('update')
@dataclass
class Visit:
    channel: Channel
    active: bool=True
    stop: object=lambda:None
class Workspace:
    def __init__(self,env,key):self.env,self.key,self.current=env,key,None
    def hide(self):
        old,self.current=self.current,None
        if old:old.active=False;old.stop()
    def select(self,channel,mode):
        self.hide();visit=Visit(channel);self.current=visit
        def decoded(value):
            if visit.active:
                self.env.output("publish",self.key,value)
        def deliver(value):
            self.env.resolve('decode',channel.key,value).add_done_callback(lambda result:decoded(result.result()))
        token=channel.listen(deliver)
        visit.stop=lambda: channel.detach(token)
        channel.connect(mode)
def collect_metrics(env,key,channel):
    events=[]
    channel.connect("synchronous")
    token=channel.listen(events.append)
    def finish():channel.update();channel.detach(token);env.output('metrics',key,events)
    env.defer(finish)
