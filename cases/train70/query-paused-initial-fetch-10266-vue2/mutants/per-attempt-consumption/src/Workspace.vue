<template><section><output>{{ view }}</output></section></template>
<script>
export default {props:['session'],data(){return {view:'empty'};},created(){this.session.project=q=>{this.view=q.key+':'+q.state.status+':'+q.state.fetchStatus;};},beforeDestroy(){this.session.dispose();},methods:{subscribe(key,options){return this.session.subscribe(key,options);},unsubscribe(h){this.session.unsubscribe(h);},online(v){this.session.online(v);},focus(v){this.session.focus(v);},snapshot(key){return this.session.snapshot(key);},dispose(){this.session.dispose();}}};
</script>
