import React, {forwardRef,useRef,useState,useMemo,useImperativeHandle,useEffect} from 'react';
import {trailing,bindConfirmation} from './services.js';
export default forwardRef(function EditorialDesk({services},ref) {
  const visit=useRef(null), [revision,rerender]=useState(0);
  const api=useMemo(()=>({env: services, navigation: 0, getVisit: ()=>visit.current,
    setVisit(value) { visit.current=value; rerender(n=>n+1); },
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
  
  const visit = this.getVisit(); if (!visit) return null;
  const snapshot = {id: visit.id, text: visit.text};
  visit.task.flush();
  
  
  
  const receipt = this.env.archive.capture(snapshot);
  const confirmation=bindConfirmation(()=>this.getVisit(),receipt=>this.env.renderSubmission(receipt));
  confirmation.show(receipt);
  return receipt;
},

  }),[services]);
  useImperativeHandle(ref,()=>({open: id=>api.open(id),edit: text=>api.edit(text),close: ()=>api.close(),submit: ()=>api.submit()}),[api]);
  useEffect(()=>()=>api.close(),[api]);
  return <section data-revision={revision}><textarea defaultValue="" onChange={event=>api.edit(event.target.value)}/><button onClick={()=>api.submit()}>Accept publication copy</button></section>;
});
