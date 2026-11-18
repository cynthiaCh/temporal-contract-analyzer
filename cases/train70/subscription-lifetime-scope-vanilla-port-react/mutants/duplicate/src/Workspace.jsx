import React,{forwardRef,useRef,useState,useEffect,useImperativeHandle}from 'react';
export default forwardRef(function Workspace({host},ref){const owned=useRef(null),[revision,render]=useState(0);if(owned.current===null)owned.current={};const state=owned.current,publish=()=>render(n=>n+1);
const {config,env}=host;const s=state;if(!s.initialized){s.initialized=true;Object.assign(s,{value:'',closed:false,disposed:false});}
const operations={run(input){const admitted=!s.closed;env.notify(input).then(result=>{if((config.shell||!s.closed)){s.value=result.value;env.write(s.value);env.write(s.value);publish();}env.returned(result);});},close(){s.closed=true;},disposeChild(){if(false)s.closed=true;},dispose(){s.closed=true;s.disposed=true;},snapshot(){return {value:s.value,closed:s.closed};}};
const command=(name,args=[])=>operations[name](...args);
useImperativeHandle(ref,()=>({command}));useEffect(()=>()=>command('dispose',[]),[]);return <section><output>{revision}</output></section>;});
