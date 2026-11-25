'use strict';
const vscode = acquireVsCodeApi();
const $ = id => document.getElementById(id);
let entries = [], taxonomy = {}, selected, dirty = false, busy = false;
const fields = [['title', 'Title'], ['abstract', 'Abstract (used for retrieval)'], ['applicability', 'Applicability conditions'], ['event_relation', 'Recommendation'], ['preservation', 'Preservation requirements'], ['exclusion', 'Exclusions'], ['verification', 'Verification'], ['labels', 'Obligation labels'], ['requires', 'Required mechanisms'], ['excludes', 'Excluded mechanisms']];
function mark(value) { dirty = value; $('dirty').textContent = value ? 'Unsaved changes' : ''; }
function confirmChange(text) {
  return new Promise(resolve => {
    const dialog = document.createElement('dialog'), description = document.createElement('p');
    description.textContent = text; dialog.append(description);
    for (const [label, answer] of [['Cancel', false], ['Continue', true]]) {
      const button = document.createElement('button'); button.textContent = label;
      button.onclick = () => { dialog.close(); dialog.remove(); resolve(answer); }; dialog.append(button);
    }
    dialog.oncancel = event => { event.preventDefault(); dialog.remove(); resolve(false); };
    document.body.append(dialog); dialog.showModal();
  });
}
async function leave() { return !busy && (!dirty || await confirmChange('Discard unsaved changes?')); }
function send(type, extra = {}) { vscode.postMessage({type, ...extra}); }
function setBusy(value) { busy = value; $('save').disabled = value; for (const field of $('fields').querySelectorAll('input, textarea, select')) field.disabled = value; }
function message(text) { $('message').textContent = text; }
function categories() {
  const before = $('category').value;
  $('category').replaceChildren();
  for (const name of ['', ...new Set(entries.map(e => e.category))]) {
    const option = document.createElement('option'); option.value = name; option.textContent = name || 'All categories'; $('category').append(option);
  }
  $('category').value = before;
}
function render() {
  const query = $('search').value.toLowerCase(), category = $('category').value;
  $('list').replaceChildren();
  for (const entry of entries.filter(e => (!category || e.category === category) && JSON.stringify(e.record).toLowerCase().includes(query))) {
    const button = document.createElement('button'); button.textContent = entry.record.title; button.title = entry.category;
    button.className = entry.id === selected?.id ? 'selected' : '';
    button.onclick = async () => { if (await leave()) edit(entry); }; $('list').append(button);
  }
}
function edit(entry) {
  selected = entry; mark(false); $('history-list').hidden = true; $('editor').hidden = false;
  $('identity').textContent = entry ? `${entry.id} · ${entry.category}` : 'New personal experience';
  $('notice').textContent = entry?.record.pending_revision ? 'An automatic revision suggestion exists. Saving here replaces it with your content.' : entry && entry.record.review?.decision !== 'accept' ? 'Suggestion: save to add this content to your usable library.' : 'Save applies your content directly. No review is required.';
  $('fields').replaceChildren();
  if (entry) {
    const source = document.createElement('details'), title = document.createElement('summary'), body = document.createElement('pre');
    title.textContent = 'Source information';
    body.textContent = JSON.stringify({file: entry.file, evidence: entry.record.evidence_ref || null, origin: entry.record.learning?.origin || null}, null, 2);
    source.append(title, body); $('fields').append(source);
  }
  for (const [key, title] of fields) {
    const label = document.createElement('label'); label.textContent = title;
    const array = ['labels', 'requires', 'excludes'].includes(key);
    const input = document.createElement(array ? 'select' : key === 'title' ? 'input' : 'textarea');
    if (array) {
      input.multiple = true; input.size = 5;
      const options = key === 'labels' ? (taxonomy.codebook || []).map(row => [row.code, `${row.code} · ${row.family}`]) : Object.keys(taxonomy.mechanism_predicates || {}).map(code => [code, code.replaceAll('_', ' ')]);
      for (const [code, text] of options) { const option = document.createElement('option'); option.value = code; option.textContent = text; input.append(option); }
    } input.id = `field-${key}`; input.required = !['labels', 'excludes'].includes(key);
    let value = entry?.record[key];
    if (key === 'abstract') value = entry?.record.summary?.text;
    if (array) { for (const option of input.options) option.selected = (value || []).includes(option.value); }
    else input.value = value || '';
    input.oninput = () => mark(true); label.append(input); $('fields').append(label);
  }
  $('delete').disabled = !entry; render();
  vscode.setState({id: entry?.id});
}
$('search').oninput = render; $('category').onchange = render;
$('new').onclick = async () => { if (await leave()) edit(null); };
for (const type of ['choose', 'reload', 'history']) $(type).onclick = async () => { if (await leave()) send(type); };
$('editor').onsubmit = event => {
  event.preventDefault(); if (busy) return;
  try {
    const record = {};
    for (const [key] of fields) record[key] = ['labels', 'requires', 'excludes'].includes(key) ? Array.from($(`field-${key}`).selectedOptions, option => option.value) : $(`field-${key}`).value.trim();
    record.expert_questions = selected?.record.summary?.expert_questions || 'None.';
    setBusy(true);
    send('change', {change: {action: 'save', id: selected?.id || `personal-${crypto.randomUUID()}`, revision: selected?.revision ?? null, record}});
  } catch (error) { message(error.message); }
};
$('delete').onclick = async () => {
  if (!selected || !await leave() || !await confirmChange('Delete this experience? You can restore its content from History.')) return;
  setBusy(true); send('change', {change: {action: 'delete', id: selected.id, revision: selected.revision}});
};
window.addEventListener('message', async event => {
  const data = event.data;
  if (data.type === 'choose-request') { if (await leave()) send('choose'); }
  else if (data.type === 'loaded' || data.type === 'saved') {
    entries = data.entries; taxonomy = data.taxonomy; setBusy(false); categories();
    if (data.store) $('store').textContent = data.store;
    const id = data.type === 'saved' ? data.id : selected?.id || vscode.getState()?.id;
    edit(entries.find(e => e.id === id) || entries[0] || null);
    message(data.type === 'saved' ? 'Saved. Future uses read the current content; existing run snapshots stay unchanged.' : `${entries.length} experiences`);
  } else if (data.type === 'select') { if (await leave()) edit(entries.find(e => e.id === data.id) || null); }
  else if (data.type === 'error') { setBusy(false); message(data.message); }
  else if (data.type === 'history') {
    $('editor').hidden = true; $('history-list').hidden = false; $('history-list').replaceChildren();
    for (const row of data.history.sort((a,b) => b.at.localeCompare(a.at))) {
      const button = document.createElement('button'); button.textContent = `${row.at} · ${row.action} · ${row.record.title}`;
      button.onclick = () => {
        const current = entries.find(e => e.id === row.id);
        edit({...row, revision: current?.revision ?? null}); mark(true);
        message('Historical content loaded. Save to restore it.');
      };
      $('history-list').append(button);
    }
    if (!data.history.length) $('history-list').textContent = 'No saved history yet.';
  }
});
edit(null); send('ready');
