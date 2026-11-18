<template><section data-business="Localization asset upload"><output>{{ owner.fileId || 'closed' }}:{{ owner.attemptId || 0 }}</output></section></template>
<script>
import {Session} from './session.js';
export default {props:['host'],data(){return {owner:{fileId:null,attemptId:null}};},created(){this.session=new Session(this.host,s=>{this.owner=s;});},beforeDestroy(){this.session.dispose();},methods:{select(f){return this.session.select(f);},retry(){return this.session.retry();},hide(){this.session.hide();},dispose(){this.session.dispose();},snapshot(){return this.session.snapshot();}}};
</script>
