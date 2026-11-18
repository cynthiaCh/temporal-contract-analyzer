<template><section><textarea :value="current ? current.text : ''" @input="edit($event.target.value)"></textarea><button @click="submit">Accept translation</button></section></template>
<script>
import {trailing,bindConfirmation} from './services.js';
export default {
  props: ['services'],
  data() { return {current: null, navigation: 0, env: this.services}; },
  beforeDestroy() { this.close(); },
  methods: { getVisit() { return this.current; }, setVisit(value) { this.current=value; },
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
  
  if(!confirmation.isActive())return null;
  
  const receipt = this.env.archive.capture(snapshot);
  
  confirmation.show(receipt);
  return receipt;
},

  },
};
</script>
