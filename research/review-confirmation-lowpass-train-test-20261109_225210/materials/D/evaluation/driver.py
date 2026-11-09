"""Trusted RPC driver, never in base or solver materialization."""
import importlib.util
import json
import sys

spec = importlib.util.spec_from_file_location('candidate', sys.argv[1] + '/src/workflow.py')
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def write(value):
    print(json.dumps(value), flush=True)

class Environment:
    def __init__(self):
        self.store = None
        self.archive = module.Archive()
        self.callbacks = {}
        self.serial = 0
        self.workspace = self.preview = None

    def call(self, kind, *args):
        write(dict(call=kind, args=args))
        while True:
            message = json.loads(sys.stdin.readline())
            if 'reply' in message:
                return message['reply']
            self.dispatch(message)

    def schedule(self, callback, delay):
        self.serial += 1
        self.callbacks[self.serial] = callback
        return self.call('schedule', self.serial, delay)

    def cancel(self, handle):
        self.call('cancel', handle)

    def output(self, kind, value):
        self.call(kind, value)

    def write(self, key, text):
        return self.call('write', key, text)

    def capture(self, snapshot):
        return self.call('capture', snapshot)

    def dispatch(self, message):
        method, args = message['method'], message['args']
        result = None
        if method == 'storeInit': self.store = module.Store(args[0])
        elif method == 'storeRead': result = self.store.read(*args)
        elif method == 'storeWrite': result = self.store.write(*args)
        elif method == 'storeSubscribe': result = self.store.subscribe(lambda event: self.call('subscriber', args[0], event))
        elif method == 'storeUnsubscribe': self.store.stop(*args)
        elif method == 'archiveCapture': result = self.archive.capture(*args)
        elif method == 'archiveSubscribe':result=self.archive.subscribe(lambda event:self.call('subscriber',args[0],event))
        elif method == 'archiveUnsubscribe':self.archive.stop(*args)
        elif method == 'archiveList': result = self.archive.list()
        elif method == 'init': self.workspace = module.Workspace(self)
        elif method == 'previewInit': self.preview = module.Preview(self)
        elif method == 'previewQuery': self.preview.query(*args)
        elif method == 'previewHide': self.preview.hide()
        elif method == 'invoke': self.callbacks.pop(args[0])()
        else: result = getattr(self.workspace, method)(*args)
        write(dict(result=result))

env = Environment()
for line in sys.stdin:
    env.dispatch(json.loads(line))
