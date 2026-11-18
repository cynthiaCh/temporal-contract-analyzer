<template><section><textarea :value="visit ? visit.text : ''" @input="edit($event.target.value)"></textarea><button @click="submit">Accept worksheet</button></section></template>
<script>
import {shallowRef, onBeforeUnmount} from 'vue3';
import {trailing,bindConfirmation} from './services.js';
export default {
  props: ['services'],
  setup(props) {
    const visit=shallowRef(null);
    const api={env: props.services, navigation: 0, getVisit: ()=>visit.value, setVisit: value=>{visit.value=value;},
retire() {
  const leaving = this.getVisit(); this.setVisit(null);
  if (leaving) leaving.stop();
  this.env.renderDocument(null);
  if (leaving) leaving.task.flush();
},
open(id) {
  this.env.renderSubmission(null);
  const request = ++this.navigation;
  this.retire();
  if (request !== this.navigation) return;
  const stop = this.env.store.subscribe(event => { if (event.id === id) this.env.renderStatus(event); });
  const task = trailing(this.env.timers, 120, text => this.env.store.write(id, text));
  const visit = {id, text: this.env.store.read(id), stop, task};
  this.setVisit(visit); this.env.renderDocument({id, text: visit.text});
},
edit(text) {
  const visit = this.getVisit(); if (!visit) return;
  visit.text = text;
  visit.task.push(text);
},
close() { this.env.renderSubmission(null); ++this.navigation; this.retire(); },
submit() {
  const confirmation=bindConfirmation(()=>this.getVisit(),receipt=>this.env.renderSubmission(receipt));
  const visit = this.getVisit(); if (!visit) return null;
  const snapshot = {id: visit.id, text: visit.text};
  visit.task.flush();
  
  
  
  const receipt = this.env.archive.capture(snapshot);
  
  confirmation.show(receipt);
  return receipt;
},

    };
    onBeforeUnmount(()=>api.close());
    return {visit,open: id=>api.open(id),edit: text=>api.edit(text),close: ()=>api.close(),submit: ()=>api.submit()};
  },
};
</script>
