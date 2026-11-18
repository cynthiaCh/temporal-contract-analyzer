import{first_match}from"./search.js";
import React,{forwardRef,useRef,useState,useEffect,useImperativeHandle}from 'react';
export default forwardRef(function Workspace({host},ref){const owned=useRef(null),[revision,render]=useState(0);if(owned.current===null)owned.current={};const state=owned.current,publish=()=>render(n=>n+1);
const {env}=host,s=state;if(!s.initialized){s.initialized=true;Object.assign(s,{done:false,outcome:null,disposed:false});}
const operations={start(){first_match(env.records,env.predicate).then(value=>{s.done=true;s.outcome={kind:'return',value,message:null};publish();},error=>{s.done=true;s.outcome={kind:error.cancelled?'cancelled':'error',value:null,message:error.cancelled?null:error.message};publish();});},cancel(){env.records.abort();},snapshot(){return {done:s.done,...(s.outcome||{})};},dispose(){s.disposed=true;}};const command=(name,args=[])=>operations[name](...args);
useImperativeHandle(ref,()=>({command}));useEffect(()=>()=>command('dispose',[]),[]);return <section><output>{revision}</output></section>;});
