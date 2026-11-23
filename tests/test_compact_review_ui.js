// Synthetic review responses exercise presentation; no real review is submitted.
const assert = require('node:assert/strict');
const {test} = require('node:test');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');

test('counts and filters separate active guidance from history and refresh all merge targets', async () => {
  const element = () => ({value:'', hidden:false, textContent:'', handlers:{},
    classList:{toggle(){}}, addEventListener(name, handler) { this.handlers[name] = handler; }});
  function card(id, lifecycle, category) {
    const review = lifecycle === 'pending' ? {decision:'pending', reviewer:null, at:null} : {decision:'accept', reviewer:'Fixture', at:'fixture-time'};
    const form = element();
    form.dataset = {id, record:'fixture-hash', review:JSON.stringify(review)};
    form.elements = {reviewer:{value:'Fixture'}, decision:{value:'accept'}};
    form.reportValidity = () => true;
    const button = element(), status = element();
    form.querySelector = () => button;
    const result = {dataset:{state:review.decision, lifecycle, category}, hidden:false,
      querySelector: selector => selector === 'form[data-id]' ? form : status};
    form.closest = () => result;
    return {result, form};
  }
  const entries = [card('old-a','active','Alpha'), card('old-b','active','Alpha'),
    card('historic','superseded','Beta'), card('merged','pending','Alpha')];
  const elements = Object.fromEntries(['compact-filter','compact-category','compact-counts','compact-empty','message'].map(id => [id,element()]));
  elements['compact-filter'].value = 'all';
  const context = vm.createContext({document:{
    querySelectorAll: selector => selector.startsWith('article') ? entries.map(x => x.result) : selector === 'form[data-id]' ? entries.map(x => x.form) : [],
    querySelector: selector => elements[selector.slice(1)]},
    fetch: async () => ({ok:true, json:async () => ({review:{decision:'accept', reviewer:'Fixture', at:'fixture-time'},
      record_sha256:'fixture-hash', file:'fixture.json',
      lifecycle:{active_ids:['merged'],superseded_ids:['old-a','old-b','historic'],unresolved_ids:[]}})})});
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../temporal_contract_analyzer/web/compact-review.js'),'utf8'),context);
  assert.equal(elements['compact-counts'].textContent,'Active 2 · Pending review 1');
  elements['compact-category'].value = 'Alpha';
  elements['compact-category'].handlers.change({});
  assert.equal(elements['compact-counts'].textContent,'Active 2 · Pending review 1');
  elements['compact-filter'].value = 'pending';
  elements['compact-filter'].handlers.change({});
  assert.deepEqual(entries.map(x => x.result.hidden),[true,true,true,false]);
  await entries[3].form.handlers.submit({preventDefault(){}});
  assert.equal(elements['compact-counts'].textContent,'Active 1 · Pending review 0');
  assert.equal(entries[0].result.dataset.lifecycle,'superseded');
  elements['compact-filter'].value = 'all';
  elements['compact-filter'].handlers.change({});
  assert.deepEqual(entries.map(x => x.result.hidden),[true,true,true,false]);
  elements['compact-category'].value = '';
  elements['compact-category'].handlers.change({});
  assert.equal(elements['compact-counts'].textContent,'Active 1 · Pending review 0');
});
