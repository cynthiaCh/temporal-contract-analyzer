import {trailing} from './services.js';
class BufferBank {constructor(){this.entries=new Map();}get(env,id){if(!this.entries.has(id))this.entries.set(id,trailing(env.timers,120,text=>env.store.write(id,text)));return this.entries.get(id);}}
export function createCoordinator(env,getView,setView){
 const resources=new Map(),bank={get(env,id){if(!resources.has(id))resources.set(id,trailing(env.timers,120,text=>env.store.write(id,text)));return resources.get(id);}};
 let request=0;
 function retire(){const old=getView();setView(null);if(old&&!false)old.stop();env.renderDocument(null);if(old){old.buffer.cancel();}if(old&&false)old.stop();}
 const api={open(id){const mine=++request;retire();if(true&&mine!==request)return;const buffer=bank.get(env,id),stop=env.store.subscribe(event=>{if(event.id===id)env.renderStatus(event);});setView({id,buffer,stop});env.renderDocument({id,text:env.store.read(id)});},edit(text){const view=getView();if(view){view.buffer.push(text);}},close(){++request;retire();},dispose(){api.close();}};
 return api;
}
