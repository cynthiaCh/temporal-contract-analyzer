class PublicationWindow {constructor(){this.arrived=0;this.published=0;}arrive(){return ++this.arrived;}publish(order){if(order<=this.published)return false;this.published=order;return true;}}
// A session owns panel visits; physical attempts keep their own cancellation.
export class Session {
 constructor(host,onState=()=>{}) {this.host=host;this.onState=onState;this.visit=null;this.serial=0;this.attempts=0;this.tasks=new Map();this.disposed=false;}
 current(v) {return this.visit===v;}
 enqueue(v,kind) {
  const n=++this.attempts, entry={fileId:v.file.id,attemptId:n,visitId:v.id,kind};
  
  this.host.record(entry);
  const window=v.window;const progress={admit:()=>window.arrive(),active:()=>this.current(v),audit:frame=>this.host.recordProgress?.({fileId:v.file.id,attemptId:n,frame}),
   view:(frame,order)=>{if(this.current(v)){this.host.showProgress?.({fileId:v.file.id,attemptId:n,frame});this.onState(this.snapshot());}}};
  const h=createAttempt(v.file,n,this.host.transport,this.host.onCancel,progress);this.tasks.set(n,h);return h;
 }
 notice(v,h){ this.host.showQueued({fileId:v.file.id,attemptId:h.attemptId,visitId:v.id,status:'queued'});}
 release(v){const h=v.handle;v.handle=null;if(h)h.cancel();}
 select(file){if(this.disposed)return null;const request=++this.serial,old=this.visit;this.visit=null;if(old)this.release(old);
  if(this.disposed||this.serial!==request)return null;const v={id:request,file,handle:null,window:new PublicationWindow()};this.visit=v;
  const h=this.enqueue(v,'select');if(this.current(v)){v.handle=h;this.notice(v,h);}else h.cancel();this.onState(this.snapshot());return h;}
 retry(){const v=this.visit;if(!v||!v.handle||this.disposed)return null;v.handle.cancel();
  const accepted=v;const h=this.enqueue(accepted,'retry');if(this.current(accepted))accepted.handle=h;else h.cancel();
  if(this.current(accepted))this.notice(accepted,h);this.onState(this.snapshot());return h;}
 hide(){this.serial++;const old=this.visit;this.visit=null;if(old)this.release(old);this.onState(this.snapshot());}
 dispose(){if(this.disposed)return;this.disposed=true;this.hide();for(const h of this.tasks.values())h.cancel();}
 snapshot(){const v=this.visit;return {visitId:v?v.id:null,fileId:v?v.file.id:null,attemptId:v&&v.handle?v.handle.attemptId:null,disposed:this.disposed,attempts:this.attempts};}
}
export function createAttempt(file,attemptId,transport,onCancel,progress={}) {
 const controller=new AbortController();let stop=()=>{};
 controller.signal.addEventListener('abort',()=>{stop();onCancel({file,attemptId,signal:controller.signal});},{once:true});
 transport({file,attemptId,signal:controller.signal});
 const feed=file.progressFeed;
 if(feed){const listener=event=>{ if(controller.signal.aborted||!progress.active())return;const order=progress.admit?.()??0;
   const deliver=frame=>{ progress.audit?.(frame);progress.view?.(frame,order);};
   const decoded=feed.decode(event.detail);if(decoded&&typeof decoded.then==='function')decoded.then(deliver);else deliver(decoded);};
  feed.target.addEventListener('progress',listener);feed.start();
  stop=()=>feed.target.removeEventListener('progress',listener);if(controller.signal.aborted)stop();}
 return {file,attemptId,signal:controller.signal,cancel(){if(!controller.signal.aborted)controller.abort();}};
}

export function collectProgressTelemetry(feed,recordDelta){
 const listener=event=>{const value=feed.decode(event.detail);if(value&&typeof value.then==='function')value.then(recordDelta);else recordDelta(value);};
 feed.start();feed.target.addEventListener('progress',listener);
 return ()=>feed.target.removeEventListener('progress',listener);
}
