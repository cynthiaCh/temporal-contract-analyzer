'use strict';
const fs=require('fs'),cp=require('child_process'),{StringDecoder}=require('string_decoder');
module.exports=function(command,options){
 const child=cp.spawn(command[0],command.slice(1),{...options,stdio:['pipe','pipe','inherit']});child.unref();child.stdin.unref();child.stdout.unref();
 child.stdin._handle.setBlocking(true);child.stdout._handle.setBlocking(true);
 const input=child.stdin._handle.fd,output=child.stdout._handle.fd,decoder=new StringDecoder('utf8');let buffer='',serial=0;const envs=new Map();let activeEnv;
 function read(){while(!buffer.includes('\n')){const b=Buffer.alloc(4096),n=fs.readSync(output,b,0,b.length,null);if(!n)throw Error('native EOF');buffer+=decoder.write(b.subarray(0,n));}const i=buffer.indexOf('\n'),line=buffer.slice(0,i);buffer=buffer.slice(i+1);return JSON.parse(line);}
 function send(x){fs.writeSync(input,JSON.stringify(x)+'\n');}
 function request(method,...args){send({method,args});for(;;){const m=read();if(Object.prototype.hasOwnProperty.call(m,'result'))return m.result;const a=m.args;let reply;
 if(m.call==='schedule')reply=activeEnv.schedule(()=>request('invoke',a[0],null),a[1]);
 else if(m.call==='cancel')reply=activeEnv.cancel(a[0]);
 else if(m.call==='defer'){queueMicrotask(()=>request('invoke',a[0],null));reply=null;}
 else {const env=envs.get(a[0]);if(!env)throw Error('missing host');if(env[m.call]){const result=env[m.call](a[1]);if(result&&typeof result.then==='function'){result.then(v=>request('invoke',a[2],v));reply={deferred:true};}else reply={deferred:false,value:result};}else throw Error('unknown host call '+m.call);}
 send({reply:reply===undefined?null:reply});}}
 return {createController(config,env){const id=++serial;envs.set(id,env);activeEnv=env;request('create',id,config);return {call(name,...a){activeEnv=env;return request('call',id,name,a);},dispose(){activeEnv=env;request('call',id,'dispose',[]);}};},finish(){child.stdin.end();}};
};
