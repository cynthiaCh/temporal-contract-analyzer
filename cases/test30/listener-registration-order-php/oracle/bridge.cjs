'use strict';
// Trusted reentrant RPC transport; candidate owns source dispatch and visit policy.
const fs=require('fs'),cp=require('child_process'),{StringDecoder}=require('string_decoder');
module.exports=function(command,options){
 const child=cp.spawn(command[0],command.slice(1),{...options,stdio:['pipe','pipe','inherit']});
 child.stdin._handle.setBlocking(true);child.stdout._handle.setBlocking(true);
 const input=child.stdin._handle.fd,output=child.stdout._handle.fd,decoder=new StringDecoder('utf8');let buffer='',serial=0;
 const feeds=new Map(),hosts=new Map(),metrics=new Map();
 function read(){while(!buffer.includes('\n')){const b=Buffer.alloc(4096),n=fs.readSync(output,b,0,b.length,null);if(!n)throw Error('native EOF before reply');buffer+=decoder.write(b.subarray(0,n));}const at=buffer.indexOf('\n'),line=buffer.slice(0,at);buffer=buffer.slice(at+1);return JSON.parse(line);}
 function send(v){fs.writeSync(input,JSON.stringify(v)+'\n');}
 function request(method,...args){send({method,args});for(;;){const m=read();if(Object.prototype.hasOwnProperty.call(m,'result'))return m.result;if(m.error)throw Error(m.error);const a=m.args;let reply=null;
 switch(m.call){
 case 'defer':queueMicrotask(()=>request('invoke',a[0],null));break;
 case 'decode':{const decoded=feeds.get(a[0]).decode(a[1]);if(decoded&&typeof decoded.then==='function'){decoded.then(value=>request('invoke',a[2],value));reply={deferred:true};}else reply={deferred:false,value:decoded};break;}
 case 'publish':{const h=hosts.get(a[0]);h.publish(a[1],h.api);break;}
 case 'metrics':metrics.get(a[0])({events:a[1]});metrics.delete(a[0]);break;
 default:throw Error('unknown native sink '+m.call);
 }send({reply:reply===undefined?null:reply});}}
 function createPresenceChannel(token,{decode=value=>value}={}){const id=++serial;request('feed',id,token);const f={decode,key:id,target:{listenerCount:()=>request('listeners',id)},connect:mode=>request('start',id,mode),emitUpdate:()=>request('delta',id)};feeds.set(id,f);return f;}
 return {createPresenceChannel,
 createWorkspaceNavigation(publish){const id=++serial,api={select:(feed,mode='synchronous')=>request('select',id,feed.key,mode),hide:()=>request('hide',id),dispose:()=>request('hide',id)};hosts.set(id,{publish,api});request('workspace',id);return api;},
 collectMetrics(token){const f=createPresenceChannel(token),id=++serial;return new Promise(resolve=>{metrics.set(id,resolve);request('metrics',id,f.key);});},
 finish(){child.stdin.end();}
 };
};
