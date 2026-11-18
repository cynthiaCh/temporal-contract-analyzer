class Controller:
    def __init__(self,env,key,config):self.env,self.key,self.shell=env,key,config['shell'];self.value='';self.closed=False
    def run(self,input):
        admitted=not self.closed
        def finish(future):
            result=future.result()
            if True:
                self.value=result['value'];self.env.output('write',self.key,self.value)
                pass
            self.env.output('returned',self.key,result)
        self.env.resolve('notify',self.key,input).add_done_callback(finish)
    def close(self):self.closed=True
    def disposeChild(self):
        if False:self.close()
    def dispose(self):self.close()
    def snapshot(self):return dict(value=self.value,closed=self.closed)
