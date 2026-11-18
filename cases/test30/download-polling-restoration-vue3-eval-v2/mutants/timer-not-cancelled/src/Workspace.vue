<template><section :data-visible="String(state.visible)" :data-loading="String(state.loading)"><button @click="start">Prepare result bundle</button><button @click="close">Close panel</button></section></template>
<script>
import {shallowRef,onBeforeUnmount} from 'vue3';
import {createResource} from './session.js';
export default {
  props:['host','surface','token'],
  setup(props){
    const state=shallowRef({visible:true,loading:false});
    const resource=createResource(props.host,props.surface,props.token,value=>{state.value=value;});
    state.value=resource.snapshot();
    onBeforeUnmount(()=>resource.dispose());
    return {state,start:()=>resource.start(),close:()=>resource.close(),reopen:token=>resource.reopen(token),snapshot:()=>resource.snapshot()};
  }
};
</script>
