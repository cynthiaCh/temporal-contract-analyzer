// The service fulfills asynchronously with false (pending) or true (ready).
// Timers run on a later turn; the host owns scheduling, not response policy.
class Resource {
  constructor(host, token, notify = () => {}) {
    this.host=host; this.notify=notify; this.generation=0; this.timer=null; this.disposed=false;
    this.state={visible:true,loading:false,retryScheduled:false,checkCount:0,completed:[],token};
  }
  snapshot(){return {...this.state,completed:[...this.state.completed]};}
  publish(){if(!this.disposed){this.host.publish(this.snapshot());this.notify(this.snapshot());}}
  cancelRetry(){if(this.timer!==null)this.host.cancel(this.timer);this.timer=null;this.state.retryScheduled=false;}
  invalidate(){this.generation++; this.state.loading=false;}
  start(){this.invalidate();this.state.visible=true;this.check(this.generation);}
  reopen(token){this.invalidate();this.state.token=token;this.state.visible=true;this.check(this.generation);}
  check(generation){
    const token=this.state.token;
    this.state.loading=true;this.state.checkCount++;this.publish();
    this.host.check(token).then(ready=>{
      if(this.disposed||generation!==this.generation)return;
      if(ready===true){
        this.cancelRetry();this.state.loading=false;
        if(!this.state.completed.includes(token))this.state.completed.push(token);
        this.publish();
      }else{this.pending(generation);}
    });
  }
  schedule(generation){
    this.state.retryScheduled=true;
    this.timer=this.host.schedule(()=>{
      if(this.disposed||generation!==this.generation)return;
      this.timer=null;this.state.retryScheduled=false;this.check(generation);
    });this.publish();
  }
  dispose(){this.disposed=true;this.generation++;this.cancelRetry();}
}
export class DialogResource extends Resource {
  pending(generation){this.schedule(generation);}
  close(){this.state.visible=false;this.invalidate();this.publish();}
}
export class WorkspaceJob extends Resource {
    start(){this.check(this.generation);}
  pending(generation){this.schedule(generation);}
  close(){this.state.visible=false; this.publish();}
}
export function createResource(host,surface,token,notify){
  return surface==='download'?new DialogResource(host,token,notify):new WorkspaceJob(host,token,notify);
}
