'use strict';
const fs=require('fs'),cp=require('child_process'),{StringDecoder}=require('string_decoder');
exports.connect=function(command,env){const child=cp.spawn(command[0],command.slice(1),{env,stdio:['pipe','pipe','inherit']});child.stdin._handle.setBlocking(true);child.stdout._handle.setBlocking(true);const input=child.stdin._handle.fd,output=child.stdout._handle.fd,decoder=new StringDecoder('utf8');let buffer='',next=0,closed=false;const hosts=new Map(),signals=new Map();
 function send(x){fs.writeSync(input,JSON.stringify(x)+'\n');}
 function read(){while(!buffer.includes('\n')){const b=Buffer.alloc(4096),n=fs.readSync(output,b,0,b.length,null);if(!n)throw Error('native process ended');buffer+=decoder.write(b.subarray(0,n));}const i=buffer.indexOf('\n'),line=buffer.slice(0,i);buffer=buffer.slice(i+1);return JSON.parse(line);}
 function callback(m){const [w,...a]=m.args,h=hosts.get(w),key=(q,n)=>w+':'+q+':'+n;switch(m.call){
 case 'newAttempt':signals.set(key(a[0],a[1]),new AbortController());return null;
 case 'abort':signals.get(key(a[0],a[1])).abort();return null;
 case 'defer':Promise.resolve().then(()=>{if(!closed)request('invoke',a[0],null);});return null;
 case 'schedule':return h.timers.schedule(()=>request('invoke',a[0],null),a[1]);
 case 'request':{const [q,n,getter,done]=a,context={key:q,attempt:n};Object.defineProperty(context,'signal',{enumerable:true,get(){request('invoke',getter,null);return signals.get(key(q,n)).signal;}});let value;try{value=h.queryFn(context);}catch(e){value=Promise.reject(e);}Promise.resolve(value).then(v=>{if(!closed)request('invoke',done,{ok:true,value:v});},e=>{if(!closed)request('invoke',done,{ok:false,value:String(e)});});return null;}
 default:throw Error(m.call);
 }}
 function request(method,...args){send({method,args});for(;;){const m=read();if(Object.prototype.hasOwnProperty.call(m,'result'))return m.result;const reply=callback(m);send({reply:reply===undefined?null:reply});}}
 return {createClient(host,initial={}){const w=++next;hosts.set(w,host);request('init',w,initial);return {subscribe:(q,o={})=>request('subscribe',w,q,o),unsubscribe:h=>request('unsubscribe',w,h),online:v=>request('online',w,v),focus:v=>request('focus',w,v),snapshot:q=>request('snapshot',w,q),dispose:()=>request('dispose',w)};},close(){closed=true;child.stdin.end();child.kill();}};
};
