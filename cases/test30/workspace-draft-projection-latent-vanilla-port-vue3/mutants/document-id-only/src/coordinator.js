import{createNavigationProjection}from './navigation-projection.js';
import {trailing} from './services.js';
class BufferBank {constructor(){this.entries=new Map();}get(env,id){if(!this.entries.has(id))this.entries.set(id,trailing(env.timers,120,text=>env.store.write(id,text)));return this.entries.get(id);}}
function createEditor(env,getView,setView){
 const bank=new BufferBank();
 let request=0;
 function retire(){const old=getView();setView(null);if(old&&!false)old.stop();env.renderDocument(null);if(old){old.buffer.flush();}if(old&&false)old.stop();}
 const api={open(id,visit){const mine=++request;retire();if(true&&mine!==request)return;const buffer=bank.get(env,id),stop=env.store.subscribe(event=>{if(event.id===id)env.renderStatus(event);});setView({id,visit,buffer,stop});env.renderDocument({id,visit,text:env.store.read(id)});},edit(text){const view=getView();if(view){view.buffer.push(text);}},close(){++request;retire();},dispose(){api.close();}};
 api.selection=()=>{const c=getView();return c?{id:c.id,visit:c.visit}:null;};
 return api;
}

export function createCoordinator(env,getView,setView){const editor=createEditor(env,getView,setView),projection=createNavigationProjection(env);let epoch=0,visit=0;return{select(id){const mine=++epoch,v=++visit;editor.open(id,v);if(editor.selection()?.id===id)projection.commit({id,visit:v});},selection:editor.selection,edit:editor.edit,close(){const mine=++epoch;editor.close();if(mine===epoch)projection.clear();},dispose(){editor.dispose();projection.clear();}};}
