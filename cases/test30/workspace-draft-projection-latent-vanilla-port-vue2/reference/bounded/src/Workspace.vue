<template><section>{{current?current.id:''}}</section></template>
<script>
import {createCoordinator}from './coordinator.js';
export default{props:['services'],data(){return{current:null};},created(){this.api=createCoordinator(this.services,()=>this.current,v=>{this.current=v;});},methods:{select(id){this.api.select(id);},selection(){return this.api.selection();},edit(t){this.api.edit(t);},close(){this.api.close();}},beforeDestroy(){this.api.dispose();}};
</script>
