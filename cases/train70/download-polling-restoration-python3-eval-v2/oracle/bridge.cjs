'use strict';
const cp=require('child_process'),fs=require('fs'),{StringDecoder}=require('string_decoder');
exports.connect=(command,env)=>{
 const child=cp.spawn(command[0],command.slice(1),{env,stdio:['pipe','pipe','inherit']});
 child.stdin._handle.setBlocking(true);child.stdout._handle.setBlocking(true);
 const decoder=new StringDecoder('utf8');let buffer='';
 function request(method,...args){
  fs.writeSync(child.stdin._handle.fd,JSON.stringify({method,args})+'\n');
  while(!buffer.includes('\n')){const block=Buffer.alloc(4096),n=fs.readSync(child.stdout._handle.fd,block,0,block.length,null);if(!n)throw new Error('native process exited without result');buffer+=decoder.write(block.subarray(0,n));}
  const pos=buffer.indexOf('\n'),line=buffer.slice(0,pos);buffer=buffer.slice(pos+1);
  return JSON.parse(line).result;
 }
 return {request,stop(){child.stdin.end();child.kill();}};
};
