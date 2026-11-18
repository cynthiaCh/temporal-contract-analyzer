type NativePort={call(name:string,...args:any[]):any};
export class NativeSlot<T>{
 private port:NativePort;
 private values=new Map<number,T|null>([[0,null]]);
 private serial=0;
 constructor(){const factory=(globalThis as any)[Symbol.for('native-buffer-host')];if(typeof factory!=='function')throw new Error('native buffer host required');this.port=factory();}
 get value():T|null{return this.values.get(this.port.call('get','value')) as T|null;}
 set value(v:T|null){const prior=this.port.call('get','value'),handle=++this.serial;this.values.set(handle,v);this.port.call('set','value',handle);if(prior!==0)this.values.delete(prior);}
 get present():boolean{return this.port.call('get','present');}
 set present(v:boolean){this.port.call('set','present',v);}
 get completed():boolean{return this.port.call('get','completed');}
 set completed(v:boolean){this.port.call('set','completed',v);}
 clear(closed:boolean,stopped:boolean):void{const prior=this.port.call('get','value');this.port.call('clear',closed,stopped);if(this.port.call('get','value')!==prior&&prior!==0)this.values.delete(prior);}
}
