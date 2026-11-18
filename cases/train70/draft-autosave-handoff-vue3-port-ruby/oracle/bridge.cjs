"use strict";
// Synchronous, reentrant RPC transports injected sinks and timers. Application
// state, batch callbacks, store delivery, visit identity and archive execute in
// the selected native runtime. The solver never receives this transport.
const fs = require('fs');
const cp = require('child_process');
const {StringDecoder}=require('string_decoder');
module.exports = function launch(command, options) {
  const child = cp.spawn(command[0], command.slice(1), { ...options, stdio: ['pipe','pipe','inherit'] });
  child.stdin._handle.setBlocking(true); child.stdout._handle.setBlocking(true);
  const input = child.stdin._handle.fd, output = child.stdout._handle.fd;
  let buffer = '';
  const decoder=new StringDecoder('utf8');
  const callbacks = new Map(); let serial = 0;
  let store, archive, timers, sinks;
  function read() {
    while (!buffer.includes('\n')) {
      const b = Buffer.alloc(4096); const n = fs.readSync(output, b, 0, b.length, null);
      if (!n) throw new Error('native runtime terminated before reply');
      buffer += decoder.write(b.subarray(0,n));
    }
    const at=buffer.indexOf('\n'), line=buffer.slice(0,at); buffer=buffer.slice(at+1);
    return JSON.parse(line);
  }
  function send(value) { fs.writeSync(input, JSON.stringify(value)+'\n'); }
  function request(method, ...args) {
    send({method,args});
    for (;;) {
      const message = read();
      if (Object.hasOwn(message, 'result')) return message.result;
      if (message.error) throw new Error(message.error);
      let result = null;
      const a = message.args;
      switch (message.call) {
        case 'write': result=store.write(...a); break;
        case 'subscriber': result=callbacks.get(a[0])(a[1]); break;
        case 'schedule': result=timers.schedule(()=>request('invoke',a[0]),a[1]); break;
        case 'cancel': timers.cancel(a[0]); break;
        case 'document': sinks.renderDocument(a[0]); break;
        case 'status': sinks.renderStatus(a[0]); break;
        case 'notice': sinks.renderSubmission(a[0]); break;
        case 'preview': sinks.publish(a[0]); break;
        default: throw new Error('unknown native callback '+message.call);
      }
      send({reply: result === undefined ? null : result});
    }
  }
  return {
    createDraftStore(initial) {
      request('storeInit', initial);
      return {
        read: id=>request('storeRead',id), write:(id,text)=>request('storeWrite',id,text),
        subscribe(fn) { const id=++serial; callbacks.set(id,fn); const token=request('storeSubscribe',id);
          return ()=>{request('storeUnsubscribe',token);callbacks.delete(id);}; }
      };
    },
    createWorkspace(env) {
      ({store,archive,timers}=env); sinks=env;
      const stop=store.subscribe(event=>env.onSaved(event,api));
      request('init');
      const api={}; for (const name of ['open','edit','close']) api[name]=(...a)=>request(name,...a);
      return {...api,dispose(){stop();request('dispose');}};
    },
    createSearchPreview(env) {
      sinks.publish=env.publish; request('previewInit');
      return {query:q=>request('previewQuery',q),hide:()=>request('previewHide')};
    },
  };
};
