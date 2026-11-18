<template><section><output>{{ revision }}</output></section></template>
<script>
import {shallowRef,ref,onBeforeUnmount} from 'vue3';
export default {props:['host'],setup(props,{expose}){const host=props.host,owned=shallowRef({}),state=owned.value,revision=ref(0),publish=()=>revision.value++;
const {config,env}=host;const s=state;Object.assign(s,{value:'',closed:false,disposed:false});
const operations={run(input){const admitted=!s.closed;env.notify(input).then(result=>{if(true){s.value=result.value;env.write(s.value);void 0;publish();}env.returned(result);});},close(){s.closed=true;},disposeChild(){if(false)s.closed=true;},dispose(){s.closed=true;s.disposed=true;},snapshot(){return {value:s.value,closed:s.closed};}};
const command=(name,args=[])=>operations[name](...args);
expose({command});onBeforeUnmount(()=>command('dispose',[]));return {revision};}};
</script>
