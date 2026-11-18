'use strict';
const path=require('path'),candidate=path.resolve(process.argv[2]),schedule=process.argv[3];const assertions=[],trace=[];let adapter,err=null;
const normalize=v=>v===undefined?'__undefined__':Array.isArray(v)?v.map(normalize):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).map(k=>[k,normalize(v[k])])):v;
const check=(id,actual,expected)=>assertions.push({id,actual:normalize(actual),expected:normalize(expected),passed:JSON.stringify(normalize(actual))===JSON.stringify(normalize(expected))});
(async()=>{try{
 adapter=await require('./framework-loader.cjs').load(candidate);let a,b,onValue=()=>{};const events=[],other=[];
 const env={value(v){events.push(['value',normalize(v)]);onValue(v);},error(e){events.push(['error',e]);},complete(){events.push(['complete']);}};
 a=adapter.createController({},env);b=adapter.createController({},{value:v=>other.push(['value',normalize(v)]),error:e=>other.push(['error',e]),complete:()=>other.push(['complete'])});
 let clearPresent=true;a.call('subscribe');b.call('subscribe');try{a.call('clear');check('public-clear-operation-present',null,null);}catch(e){check('public-clear-operation-present',String(e.message||e),null);clearPresent=false;}
 if(clearPresent){if(schedule==='framework-active'){
  a.call('next',19);b.call('next',31);a.call('clear');a.call('clear');check('clear-no-notification',events,[]);a.call('next',undefined);a.call('complete');b.call('complete');check('undefined-refill',events,[['value','__undefined__'],['complete']]);check('independent-instance',other,[['value',31],['complete']]);
 }else if(schedule==='framework-reentrant'){
  let once=false;onValue=()=>{if(!once){once=true;a.call('clear');a.call('subscribe');a.call('complete');}};a.call('next',17);a.call('complete');check('inline-clear-preserves-final',events,[['value',17],['value',17],['complete'],['complete']]);a.call('subscribe');check('late-value-final',events.slice(-2),[['value',17],['complete']]);
 }else if(schedule==='framework-identity'){
  const data={value:'entry'};const identities=[];let once=false;
  onValue=v=>{identities.push(v===data);if(!once){once=true;data.value='callback';a.call('clear');a.call('subscribe');}};
  a.call('next',data);data.value='after-entry';a.call('complete');data.value='later';a.call('subscribe');
  check('object-identity-preserved',identities,[true,true,true]);check('reference-remains-live',events,[['value',{value:'after-entry'}],['value',{value:'callback'}],['complete'],['complete'],['value',{value:'later'}],['complete']]);
 }else if(schedule==='framework-terminal'){
  a.call('next',23);a.call('complete');a.call('clear');a.call('subscribe');check('completed-clear-stable',events,[['value',23],['complete'],['value',23],['complete']]);b.call('error','original-error');b.call('clear');b.call('subscribe');check('errored-clear-stable',other,[['error','original-error'],['error','original-error']]);const c=adapter.createController({},env);c.call('unsubscribe');const before=c.call('snapshot');c.call('clear');check('unsubscribed-unchanged',c.call('snapshot'),before);
 }else throw Error(schedule);}
 }catch(e){err=String(e.stack||e);}finally{if(adapter)adapter.finish();}process.stdout.write(JSON.stringify({schedule,passed:err===null&&assertions.every(a=>a.passed),runtimeError:err,assertions,trace})+'\n');})();
