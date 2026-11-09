import $ from 'jquery';
import {trailing,bindConfirmation} from './services.js';
export function createWorkspace({element,...env}) {
  const host=$(element);
  host.html('<textarea></textarea><button type="button">Accept work order</button>');
  const api={env, navigation: 0, getVisit: ()=>host.data('visit') || null,
    setVisit(value) { host.data('visit',value); },
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
  host.on('workorder:open', (event,id)=>api.open(id));
  host.on('workorder:close', ()=>api.close());
  host.on('workorder:submit', ()=>api.submit());
  host.on('workorder:edit', (event,text)=>api.edit(text));
  host.on('input','textarea',event=>api.edit($(event.target).val()));
  host.on('click','button',()=>api.submit());
  return {open: id=>host.triggerHandler('workorder:open',[id]),
    close: ()=>host.triggerHandler('workorder:close'),submit: ()=>host.triggerHandler('workorder:submit') ?? null,
    edit(text) { host.find('textarea').val(text);host.triggerHandler('workorder:edit',[text]); },
    dispose() { api.close();host.off();host.removeData('visit');host.empty(); },
  };
}
