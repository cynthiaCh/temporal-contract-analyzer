<template><section><output>{{ revision }}</output></section></template>
<script>
export default {props:['host'],data(){return {state:{},revision:0};},created(){const host=this.host,state=this.state,publish=()=>this.revision++;
const {config,env}=host;const s=state;Object.assign(s,{value:'',closed:false,disposed:false});
const operations={run(input){const admitted=!s.closed;env.notify(input).then(result=>{if(admitted){s.value=result.value;env.write(s.value);void 0;publish();}env.returned(result);});},close(){s.closed=true;},disposeChild(){if(false)s.closed=true;},dispose(){s.closed=true;s.disposed=true;},snapshot(){return {value:s.value,closed:s.closed};}};
const command=(name,args=[])=>operations[name](...args);
this.command=command;},beforeDestroy(){this.command('dispose',[]);}};
</script>
