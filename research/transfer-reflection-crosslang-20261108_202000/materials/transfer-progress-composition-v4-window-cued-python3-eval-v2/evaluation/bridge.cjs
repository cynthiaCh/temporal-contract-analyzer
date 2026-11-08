'use strict';
const fs=require('fs'),cp=require('child_process'),{StringDecoder}=require('string_decoder');
exports.connect=function(command,env){
 const path=require('path'),repo=require('./native-launch.cjs').findRoot(__dirname),logDir=path.join(repo,'results/transfer-v4-window-runtime/native-launch-receipts');fs.mkdirSync(logDir,{recursive:true});const logId=process.pid+'-'+process.hrtime.bigint(),wire=[];
 const child=cp.spawn(command[0],command.slice(1),{env,stdio:['pipe','pipe','inherit']});child.stdin._handle.setBlocking(true);child.stdout._handle.setBlocking(true);
 const input=child.stdin._handle.fd,output=child.stdout._handle.fd,decoder=new StringDecoder('utf8');let buffer='',next=0,fileSerial=0,listenerSerial=0,closed=false;
 const hosts=new Map(),files=new Map(),tokens=new WeakMap(),signals=new Map(),listeners=new Map();
 const key=(w,n)=>w+':'+n;
 function descriptor(file){if(!tokens.has(file)){tokens.set(file,++fileSerial);files.set(fileSerial,file);}return {token:tokens.get(file),id:file.id,size:file.size||0,feed:!!file.progressFeed};}
 function read(){while(!buffer.includes('\n')){const b=Buffer.alloc(4096),n=fs.readSync(output,b,0,b.length,null);if(!n)throw new Error('native runtime terminated before reply');buffer+=decoder.write(b.subarray(0,n));}const at=buffer.indexOf('\n'),line=buffer.slice(0,at);buffer=buffer.slice(at+1);const value=JSON.parse(line);wire.push({direction:'native-to-host',value});return value;}
 function send(x){wire.push({direction:'host-to-native',value:x});fs.writeSync(input,JSON.stringify(x)+'\n');}
 function callback(m){const [w,...a]=m.args,host=hosts.get(w);let result=null;
  switch(m.call){
   case 'transport':{const [f,n]=a,controller=new AbortController();signals.set(key(w,n),controller);controller.signal.addEventListener('abort',()=>host.onCancel({file:files.get(f),attemptId:n,signal:controller.signal}),{once:true});host.transport({file:files.get(f),attemptId:n,signal:controller.signal});break;}
   case 'cancel':{const [f,n]=a,controller=signals.get(key(w,n));controller.abort();break;}
   case 'recordDelta':case 'record':case 'showQueued':case 'recordProgress':case 'showProgress':if(host[m.call])host[m.call](a[0]);break;
   case 'listen':{const [f,token]=a,id=++listenerSerial,listener=e=>request('invoke',token,e.detail);listeners.set(id,{f,listener});files.get(f).progressFeed.target.addEventListener('progress',listener);result=id;break;}
   case 'unlisten':{const entry=listeners.get(a[1]);if(entry){listeners.delete(a[1]);files.get(entry.f).progressFeed.target.removeEventListener('progress',entry.listener);}break;}
   case 'start':files.get(a[0]).progressFeed.start();break;
   case 'decode':{const value=files.get(a[0]).progressFeed.decode(a[1]);if(value&&typeof value.then==='function'){value.then(frame=>{if(!closed)request('invoke',a[2],frame);});result={deferred:true};}else result={deferred:false,frame:value};break;}
   default:throw new Error('unknown adapter call '+m.call);
  }return result;
 }
 function request(method,...args){send({method,args});for(;;){const m=read();if(Object.hasOwn(m,'result'))return m.result;if(m.error)throw new Error(m.error);const reply=callback(m);send({reply:reply===undefined?null:reply});}}
 function handle(w,file,n){if(n===null)return null;return {file,attemptId:n,signal:signals.get(key(w,n)).signal,cancel:()=>request('cancelHandle',w,n)};}
 return {
  collectProgressTelemetry(feed,recordDelta){const w=++next;hosts.set(w,{recordDelta});const f={id:"telemetry",size:0,progressFeed:feed};request("telemetryStart",w,descriptor(f));return ()=>request("telemetryStop",w);},
  createTransferWorkspace(host){const w=++next;hosts.set(w,host);request('init',w);return {select:file=>handle(w,file,request('select',w,descriptor(file))),retry:()=>{const n=request('retry',w);return n===null?null:{attemptId:n,signal:signals.get(key(w,n)).signal,cancel:()=>request('cancelHandle',w,n)};},hide:()=>request('hide',w),dispose:()=>request('dispose',w),snapshot:()=>request('snapshot',w)};},
  createTransfer(file,n,transport,onCancel){const w=++next;hosts.set(w,{transport,onCancel});return handle(w,file,request('standalone',w,descriptor(file),n));},
  close(){closed=true;child.stdin.end();child.once('exit',(code,signal)=>{fs.writeFileSync(path.join(logDir,logId+'.json'),JSON.stringify({command,cwd:process.cwd(),exit_code:code,termination_signal:signal,shutdown:'host requested after oracle observation',runtime_versions:require(path.join(repo,'case-clusters/transfer-retry-handoff/expansion/transfer-progress-composition-v4-window-cued/runtime-versions.json')),wire},null,2));});child.kill();}
 };
};
