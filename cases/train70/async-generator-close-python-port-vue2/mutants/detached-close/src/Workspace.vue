<template><section><output>{{ revision }}</output></section></template>
<script>
import {first_match}from "./search.js";
export default {props:['host'],data(){return {state:{},revision:0};},created(){const host=this.host,state=this.state,publish=()=>this.revision++;
const {env}=host,s=state;Object.assign(s,{done:false,outcome:null,disposed:false});
const operations={start(){first_match(env.records,env.predicate).then(value=>{s.done=true;s.outcome={kind:'return',value,message:null};publish();},error=>{s.done=true;s.outcome={kind:error.cancelled?'cancelled':'error',value:null,message:error.cancelled?null:error.message};publish();});},cancel(){env.records.abort();},snapshot(){return {done:s.done,...(s.outcome||{})};},dispose(){s.disposed=true;}};const command=(name,args=[])=>operations[name](...args);
this.command=command;},beforeDestroy(){this.command('dispose',[]);}};
</script>
