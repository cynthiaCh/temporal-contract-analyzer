import $ from 'jquery';
import {Session} from './session.js';
export function mount(host,surface,token,element){const node=$(element).attr('data-business','Facility handover archive transfer'),session=new Session(host,s=>node.find('output').text(`${s.fileId||'closed'}:${s.attemptId||0}`));node.html('<output>closed:0</output>').data('transfer-session',session);let result;
 for(const name of ['select','retry','hide'])node.on(name+'.transfer',(_,value)=>{result=session[name](value);});
 return {select:f=>{if(session.disposed)return null;node.triggerHandler('select.transfer',[f]);return result;},retry:()=>{if(session.disposed)return null;node.triggerHandler('retry.transfer');return result;},hide:()=>node.triggerHandler('hide.transfer'),snapshot:()=>session.snapshot(),dispose(){session.dispose();node.off('.transfer').removeData('transfer-session');}};
}
