'use strict';
// Trusted synchronous/reentrant transport only. Feed registry, admission,
// lifetime state and effect decisions are all in the native candidate.
const fs=require('fs'),cp=require('child_process'),{StringDecoder}=require('string_decoder');
module.exports=function(command,options){
 const child=cp.spawn(command[0],command.slice(1),{...options,stdio:['pipe','pipe','inherit']});
 child.stdin._handle.setBlocking(true);child.stdout._handle.setBlocking(true);
 const input=child.stdin._handle.fd,output=child.stdout._handle.fd,decoder=new StringDecoder('utf8');let buffer='',serial=0,frameSerial=0;
 const feeds=new Map(),hosts=new Map(),frames=new Map(),metrics=new Map();
 function read(){while(!buffer.includes('\n')){const b=Buffer.alloc(4096),n=fs.readSync(output,b,0,b.length,null);if(!n)throw Error('native EOF before reply');buffer+=decoder.write(b.subarray(0,n));}const at=buffer.indexOf('\n'),line=buffer.slice(0,at);buffer=buffer.slice(at+1);return JSON.parse(line);}
 function send(v){fs.writeSync(input,JSON.stringify(v)+'\n');}
 function pack(frame){const id=++frameSerial;frames.set(id,frame);return {...frame,__frame:id};}
 function unpack(frame){if(frame&&frame.__frame)return frames.get(frame.__frame)||frame;return frame;}
 function request(method,...args){send({method,args});for(;;){const m=read();if(Object.hasOwn(m,'result'))return m.result;if(m.error)throw Error(m.error);const a=m.args;let reply=null;
 switch(m.call){
 case 'defer':queueMicrotask(()=>request('invoke',a[0],null));break;
 case 'decode':{const f=feeds.get(a[0]),decoded=f.decode(a[1]);if(decoded&&typeof decoded.then==='function'){decoded.then(value=>request('invoke',a[2],pack(value)));reply={deferred:true};}else reply={deferred:false,value:pack(decoded)};break;}
 case 'paint':{const host=hosts.get(a[0]),result=host.paintRows(unpack(a[1]),host.api);if(result&&typeof result.then==='function'){result.then(()=>request('invoke',a[2],null));reply={deferred:true};}else reply={deferred:false,value:null};break;}
 case 'history':hosts.get(a[0]).history.record(unpack(a[1]));break;
 case 'count':hosts.get(a[0]).showCount(unpack(a[1]));break;
 case 'metrics':metrics.get(a[0])(a[1]);metrics.delete(a[0]);break;
 default:throw Error('unknown native sink '+m.call);
 }send({reply:reply===undefined?null:reply});}}
 return {
 createFeed(token,{decode=frame=>frame}={}){const id=++serial;request('feed',id,token);const f={decode,key:id,target:{listenerCount:()=>request('listeners',id)},start:mode=>request('start',id,mode),emitDelta:()=>request('delta',id)};feeds.set(id,f);return f;},
 createFeedWorkspace(host){const id=++serial,api={select:(feed,mode='synchronous')=>request('select',id,feed.key,mode),hide:()=>request('hide',id),dispose:()=>request('hide',id)};hosts.set(id,{...host,api});request('workspace',id);return api;},
 collectMetrics(feed){const id=++serial;return new Promise(resolve=>{metrics.set(id,resolve);request('metrics',id,feed.key);});},
 finish(){child.stdin.end();}
 };
};
