<template><section><output>{{ revision }}</output></section></template>
<script>
import {AsyncSubject}from '../rxjs/src/internal/AsyncSubject';
export default {props:['host'],data(){return {state:{},revision:0};},created(){const host=this.host,state=this.state,publish=()=>this.revision++;
const {env}=host,s=state;Object.assign(s,{subject:new AsyncSubject(),disposed:false});
function command(name,args){switch(name){case 'next':s.subject.next(args[0]);break;case 'clear':if(typeof s.subject.clear==='function')s.subject.clear();else throw Error('clear API unavailable');break;case 'complete':s.subject.complete();break;case 'error':s.subject.error(args[0]);break;case 'unsubscribe':s.subject.unsubscribe();break;case 'subscribe':return s.subject.subscribe({next:v=>env.value(v),error:e=>env.error(e),complete:()=>env.complete()});case 'snapshot':return {closed:s.subject.closed,stopped:s.subject.isStopped};case 'dispose':s.disposed=true;break;default:throw Error(name);}publish();}this.command=command;},beforeDestroy(){this.command('dispose',[]);}};
</script>
