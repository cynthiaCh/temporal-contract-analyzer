<template><section>{{current?current.id:''}}</section></template>
<script>
import {shallowRef,onBeforeUnmount}from 'vue3';import{createCoordinator}from './coordinator.js';
export default{props:['services'],setup(props,{expose}){const current=shallowRef(null),api=createCoordinator(props.services,()=>current.value,v=>current.value=v);expose(api);onBeforeUnmount(api.dispose);return{current};}};
</script>
