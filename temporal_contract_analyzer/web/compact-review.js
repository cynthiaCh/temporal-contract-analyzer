'use strict';
const cards = [...document.querySelectorAll('article[data-state]')];
const filter = document.querySelector('#compact-filter');
const category = document.querySelector('#compact-category');
const message = document.querySelector('#message');
const search = document.querySelector('#compact-search');
const summaryFilter = document.querySelector('#summary-filter');
const queue = [...document.querySelectorAll('#compact-queue button')];
let selectedId = null;
const states = {pending:'Pending review', accept:'Accepted', revise:'Revision required', reject:'Rejected'};
const viewStates = {active:'Active', pending:'Pending review', revise:'Revision required', reject:'Rejected'};
function refresh(lifecycle) {
  if (lifecycle?.superseded_ids) {
    const superseded = new Set(lifecycle.superseded_ids);
    const unresolved = new Set(lifecycle.unresolved_ids);
    for (const card of cards) {
      const form = card.querySelector('form[data-id]');
      const review = JSON.parse(form.dataset.review);
      card.dataset.state = review.decision;
      card.dataset.lifecycle = review.decision === 'accept' ? (superseded.has(form.dataset.id) ? 'superseded' : 'active') : review.decision;
      if (card.dataset.lifecycle === 'superseded') continue;
      const label = viewStates[card.dataset.lifecycle];
      let text = review.decision === 'pending' ? label : `${label} · ${review.reviewer} · ${review.at}`;
      if (unresolved.has(form.dataset.id)) text += ' · Supersession requires review; retained for retrieval for now';
      card.querySelector('.compact-status').textContent = text;
      const queueButton = queue.find(button => button.dataset.target === form.dataset.id);
      if (queueButton) queueButton.querySelector('small').textContent = card.dataset.category + ' · ' + label;
    }
  }
  const counts = Object.fromEntries(Object.keys(viewStates).map(state => [state, 0]));
  for (const card of cards) {
    if (card.dataset.lifecycle === 'superseded') {
      card.hidden = true;
      card.dataset.matches = 'false';
      continue;
    }
    const matchesCategory = !category.value || category.value === card.dataset.category;
    if (matchesCategory) counts[card.dataset.lifecycle]++;
    const matchesSummary = !summaryFilter || summaryFilter.value === 'all' || summaryFilter.value === card.dataset.summaryState;
    const query = (search?.value || '').trim().toLowerCase();
    card.hidden = !matchesCategory || (filter.value !== 'all' && filter.value !== card.dataset.lifecycle) || !matchesSummary || Boolean(query && !(card.textContent + ' ' + card.dataset.id).toLowerCase().includes(query));
    card.dataset.matches = String(!card.hidden);
  }
  document.querySelector('#compact-counts').textContent = Object.keys(viewStates)
    .filter(state => ['active', 'pending'].includes(state) || counts[state])
    .map(state => viewStates[state]+' '+counts[state]).join(' · ');
  document.querySelector('#compact-empty').hidden = cards.some(card => !card.hidden);
  if (search) selectCard(selectedId);
}
function selectCard(id) {
  const visible = cards.filter(card => card.dataset.matches === 'true');
  selectedId = visible.some(card => card.dataset.id === id) ? id : visible[0]?.dataset.id;
  for (const card of cards) card.hidden = card.dataset.id !== selectedId;
  for (const button of queue) {
    const card = cards.find(card => card.dataset.id === button.dataset.target);
    button.hidden = card?.dataset.matches !== 'true';
    button.classList.toggle('selected', button.dataset.target === selectedId);
    button.setAttribute('aria-current', button.dataset.target === selectedId ? 'true' : 'false');
  }
}
for (const button of queue) button.addEventListener('click', () => selectCard(button.dataset.target));
search?.addEventListener('input', refresh);
summaryFilter?.addEventListener('change', refresh);
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
      if (result.review.decision === 'accept') {
        const note = card.querySelector('.revision-note');
        if (note) note.hidden = true;
      }
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

for (const form of document.querySelectorAll('.summary-form')) {
  form.addEventListener('input', () => {
    form.closest('article').querySelector('.summary-status').textContent = 'Unsaved changes';
  });
  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.reportValidity()) return;
    const button = form.querySelector('button');
    button.disabled = true;
    try {
      const response = await fetch('/api/compact-summary', {
        method:'POST', headers:{'Content-Type':'application/json', 'X-TCA-Request':'local'},
        body:JSON.stringify({id:form.dataset.summaryId, expected_record:form.dataset.record,
          expected_summary:JSON.parse(form.dataset.summary), text:form.elements.text.value,
          expert_questions:form.elements.expert_questions.value, reviewer:form.elements.reviewer.value,
          decision:form.elements.decision.value})
      });
      const result = await response.json();
      if (!response.ok) throw Error(result.error || response.statusText);
      form.dataset.summary = JSON.stringify(result.summary);
      const card = form.closest('article');
      card.dataset.summaryState = result.summary.review.decision;
      card.querySelector('.summary-status').textContent = states[result.summary.review.decision];
      card.querySelector('.summary-review-meta').textContent = [result.summary.review.reviewer, result.summary.review.at].filter(Boolean).join(' · ');
      const queueButton = queue.find(button => button.dataset.target === card.dataset.id);
      if (queueButton) queueButton.querySelector('small:last-child').textContent = 'Summary · ' + states[result.summary.review.decision];
      form.elements.decision.value = '';
      message.classList.toggle('error', false);
      message.textContent = 'Summary review saved to ' + result.file + '.';
      refresh();
    } catch (error) {
      message.classList.toggle('error', true);
      message.textContent = error.message;
    } finally { button.disabled = false; }
  });
}
