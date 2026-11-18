<template><section><output>{{ view }}</output></section></template>
<script>
import {shallowRef,onBeforeUnmount} from 'vue3';
export default {props:['session'],setup(props){const view=shallowRef('empty'),session=props.session;session.project=q=>{view.value=q.key+':'+q.state.status+':'+q.state.fetchStatus;};onBeforeUnmount(()=>session.dispose());return {view,subscribe:(k,o)=>session.subscribe(k,o),unsubscribe:h=>session.unsubscribe(h),online:v=>session.online(v),focus:v=>session.focus(v),snapshot:k=>session.snapshot(k),dispose:()=>session.dispose()};}};
</script>
