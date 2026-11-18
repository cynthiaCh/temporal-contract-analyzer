<template><section data-business="Laboratory sequence transfer"><output>{{ owner.fileId || 'closed' }}:{{ owner.attemptId || 0 }}</output></section></template>
<script>
import {shallowRef,onBeforeUnmount} from 'vue3';
import {Session} from './session.js';
export default {props:['host'],setup(props){const owner=shallowRef({}),session=new Session(props.host,s=>{owner.value=s;});onBeforeUnmount(()=>session.dispose());return {owner,select:f=>session.select(f),retry:()=>session.retry(),hide:()=>session.hide(),dispose:()=>session.dispose(),snapshot:()=>session.snapshot()};}};
</script>
