class Attempt {
 constructor(number,state,options){this.number=number;this.previous={...state};this.options=options;this.controller=new AbortController();this.settled=false;this.started=false;this.consumed=false;this.retryCancelled=false;this.failures=0;this.queued=false;}
}
export class Session {
 constructor(host,initial={}){this.host=host;this.cache=new Map();this.handles=new Map();this.connected=initial.online!==false;this.focused=initial.focused!==false;this.serial=0;this.fetchSerial=0;this.project=()=>{};}
 eligible(a){return this.focused&&((a.options.networkMode||'online')==='always'||this.connected);}
 active(q,a){return q.attempt===a&&!a.settled;}
 cancel(q,a){if(a.settled)return;a.settled=true;q.state={...a.previous,fetchStatus:'idle'};a.controller.abort();this.project(q);}
 invoke(q,a){a.queued=false;if(!this.active(q,a))return;a.started=true;q.state.fetchStatus='fetching';const context={key:q.key,attempt:a.number};Object.defineProperty(context,'signal',{enumerable:true,get(){a.consumed=true;return a.controller.signal;}});let value;try{value=this.host.queryFn(context);}catch(e){value=Promise.reject(e);}Promise.resolve(value).then(value=>{if(!this.active(q,a))return;a.settled=true;q.state={...q.state,data:value,status:'success',fetchStatus:'idle'};this.project(q);},()=>{if(!this.active(q,a))return;if(!a.retryCancelled&&a.failures<(a.options.retry||0)){a.failures++;this.host.timers.schedule(()=>{if(!this.active(q,a))return;if(a.retryCancelled){a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}else if(this.eligible(a))this.invoke(q,a);else q.state.fetchStatus='paused';this.project(q);},a.options.retryDelay||10);}else{a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};}this.project(q);});this.project(q);}
 resume(q){const a=q.attempt;if(a&&this.active(q,a)&&q.state.fetchStatus==='paused'&&this.eligible(a)&&!a.queued){a.queued=true;Promise.resolve().then(()=>{a.queued=false;if(!this.active(q,a))return;if(a.failures&&a.retryCancelled){a.settled=true;q.state={...q.state,status:'error',fetchStatus:'idle'};this.project(q);return;}this.invoke(q,a);});}}
 subscribe(key,options={}){let q=this.cache.get(key);if(!q){const data=options.initialData===undefined?null:options.initialData;q={key,state:{status:data===null?'pending':'success',fetchStatus:'idle',data},observers:new Set(),attempt:null};this.cache.set(key,q);}const handle=++this.serial;this.handles.set(handle,q);q.observers.add(handle);if(q.attempt&&!q.attempt.settled){q.attempt.retryCancelled=false;this.resume(q);}else{const a=new Attempt(++this.fetchSerial,q.state,options);q.attempt=a;if((options.networkMode||'online')!=='online'||this.connected)this.invoke(q,a);else q.state.fetchStatus='paused';}this.project(q);return handle;}
 unsubscribe(handle){const q=this.handles.get(handle);if(!q)return;this.handles.delete(handle);q.observers.delete(handle);if(q.observers.size===0){const a=q.attempt;if(a&&!a.settled){if(!a.started||a.consumed)this.cancel(q,a);else a.retryCancelled=true;}}this.project(q);}
 online(value){this.connected=value;for(const q of this.cache.values())this.resume(q);}
 focus(value){this.focused=value;for(const q of this.cache.values())this.resume(q);}
 snapshot(key){return {...this.cache.get(key).state};}
 dispose(){for(const handle of [...this.handles.keys()])this.unsubscribe(handle);}
}
