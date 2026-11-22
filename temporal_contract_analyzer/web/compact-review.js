'use strict';
const cards = [...document.querySelectorAll('article[data-state]')];
const filter = document.querySelector('#compact-filter');
const category = document.querySelector('#compact-category');
const message = document.querySelector('#message');
const states = {pending:'Pending review', accept:'Accepted', revise:'Revision required', reject:'Rejected'};
const viewStates = {active:'当前有效', superseded:'历史已替代', pending:'待审核', revise:'需修改', reject:'已拒绝'};
function refresh(lifecycle) {
  if (lifecycle?.superseded_ids) {
    const superseded = new Set(lifecycle.superseded_ids);
    const unresolved = new Set(lifecycle.unresolved_ids);
    for (const card of cards) {
      const form = card.querySelector('form');
      const review = JSON.parse(form.dataset.review);
      card.dataset.state = review.decision;
      card.dataset.lifecycle = review.decision === 'accept' ? (superseded.has(form.dataset.id) ? 'superseded' : 'active') : review.decision;
      const label = viewStates[card.dataset.lifecycle];
      let text = review.decision === 'pending' ? label : `${label} · ${review.reviewer} · ${review.at}`;
      if (superseded.has(form.dataset.id)) text += ' · Superseded; excluded from new retrievals';
      else if (unresolved.has(form.dataset.id)) text += ' · Supersession requires review; retained for retrieval for now';
      card.querySelector('.compact-status').textContent = text;
    }
  }
  const counts = Object.fromEntries(Object.keys(viewStates).map(state => [state, 0]));
  for (const card of cards) {
    const matchesCategory = !category.value || category.value === card.dataset.category;
    if (matchesCategory) counts[card.dataset.lifecycle]++;
    card.hidden = !matchesCategory || (filter.value !== 'all' && filter.value !== card.dataset.lifecycle);
  }
  document.querySelector('#compact-counts').textContent = Object.keys(viewStates)
    .filter(state => ['active', 'superseded', 'pending'].includes(state) || counts[state])
    .map(state => viewStates[state]+' '+counts[state]).join(' · ');
  document.querySelector('#compact-empty').hidden = cards.some(card => !card.hidden);
}
filter.addEventListener('change', refresh);
category.addEventListener('change', refresh);
for (const form of document.querySelectorAll('form[data-id]')) {
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      const response = await fetch('/api/compact-review', {
        method:'POST', headers:{'Content-Type':'application/json', 'X-TCA-Request':'local'},
        body:JSON.stringify({id:form.dataset.id, expected_record:form.dataset.record,
          expected_review:JSON.parse(form.dataset.review), reviewer:form.elements.reviewer.value,
          decision:form.elements.decision.value})
      });
      const result = await response.json();
      if (!response.ok) throw Error(result.error || response.statusText);
      const card = form.closest('article');
      card.dataset.state = result.review.decision;
      card.querySelector('.compact-status').textContent = states[result.review.decision]+' · '+result.review.reviewer+' · '+result.review.at;
      form.dataset.review = JSON.stringify(result.review);
      form.dataset.record = result.record_sha256;
      form.elements.decision.value = '';
      message.classList.toggle('error', false);
      message.textContent = 'Review saved to '+result.file+'.';
      refresh(result.lifecycle);
    } catch (error) {
      message.classList.toggle('error', true);
      message.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
}
refresh();
