<template><section :data-visible="String(state.visible)" :data-loading="String(state.loading)"><button @click="start">Prepare translation package</button><button @click="close">Close panel</button></section></template>
<script>
import {createResource} from './session.js';
export default {
  props:['host','surface','token'],
  data(){return {state:{visible:true,loading:false},resource:null};},
  created(){this.resource=createResource(this.host,this.surface,this.token,state=>{this.state=state;});this.state=this.resource.snapshot();},
  beforeDestroy(){this.resource.dispose();},
  methods:{start(){this.resource.start();},close(){this.resource.close();},reopen(token){this.resource.reopen(token);},snapshot(){return this.resource.snapshot();}}
};
</script>
