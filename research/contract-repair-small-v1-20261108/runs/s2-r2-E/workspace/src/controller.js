import { observe } from "./observations.js";
export function createController({service,audit,render}) {
 let current=null;
 return {
  open(doc,actor){current={doc,actor,text:"",latest:null};},
  edit(text){if(current)current.text=text;},
  submit(){
   const visit=current;if(!visit)return null;
   const owner={};visit.latest=owner;
   const snapshot={doc:visit.doc,actor:visit.actor,text:visit.text};
   const done=receipt=>{observe(audit,snapshot,receipt);if(current===visit&&visit.latest===owner)render({status:"saved",doc:snapshot.doc});return receipt;};
   const failed=error=>{if(current===visit&&visit.latest===owner)render({status:"error",doc:snapshot.doc});throw error;};
   try{return Promise.resolve(service.commit(snapshot)).then(done,failed);}catch(error){return Promise.reject(error).catch(failed);}
  },
  close(){current=null;}
 };
}
