'use strict';
const cards = [...document.querySelectorAll('article[data-state]')];
const filter = document.querySelector('#compact-filter');
const category = document.querySelector('#compact-category');
const message = document.querySelector('#message');
const states = {pending:'待审核', accept:'已接受', revise:'需修改', reject:'已拒绝'};
function refresh() {
  const counts = Object.fromEntries(Object.keys(states).map(state => [state, 0]));
  for (const card of cards) {
    const matchesCategory = !category.value || category.value === card.dataset.category;
    if (matchesCategory) counts[card.dataset.state]++;
    card.hidden = !matchesCategory || (filter.value !== 'all' && filter.value !== card.dataset.state);
  }
  document.querySelector('#compact-counts').textContent = Object.keys(states).map(state => states[state]+' '+counts[state]).join(' · ');
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
      message.textContent = '审核已保存到 '+result.file+'。';
      refresh();
    } catch (error) {
      message.classList.toggle('error', true);
      message.textContent = error.message;
    } finally {
      button.disabled = false;
    }
  });
}
refresh();
