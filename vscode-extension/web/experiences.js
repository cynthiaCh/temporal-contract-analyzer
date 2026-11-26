'use strict';
const vscode = acquireVsCodeApi();
const $ = id => document.getElementById(id);
let entries = [], taxonomy = {}, selected, dirty = false, busy = false;
const fields = [['title', 'Title'], ['abstract', 'Abstract (used for retrieval)'], ['applicability', 'Applicability conditions'], ['event_relation', 'Recommendation'], ['preservation', 'Preservation requirements'], ['exclusion', 'Exclusions'], ['verification', 'Verification'], ['labels', 'Obligation labels'], ['requires', 'Required mechanisms'], ['excludes', 'Excluded mechanisms']];
function fitField(input) {
  input.style.height = 'auto';
  input.style.height = `${input.scrollHeight + input.offsetHeight - input.clientHeight}px`;
}
function fitAutoSizeFields() { for (const input of $('fields').querySelectorAll('textarea[data-autosize]')) fitField(input); }
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
function message(text, error = false) { $('message').textContent = text; $('message').classList.toggle('error', error); }
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
  const matches = entries.filter(e => (!category || e.category === category) && JSON.stringify(e.record).toLowerCase().includes(query));
  $('count').textContent = String(entries.length);
  for (const entry of matches) {
    const button = document.createElement('button'); button.title = entry.record.title;
    button.className = `entry${entry.id === selected?.id ? ' selected' : ''}`;
    button.setAttribute('aria-current', entry.id === selected?.id ? 'true' : 'false');
    const title = document.createElement('span'), preview = document.createElement('span'), meta = document.createElement('span');
    title.className = 'entry-title'; title.textContent = entry.record.title;
    preview.className = 'entry-preview'; preview.textContent = entry.record.summary?.text || '';
    meta.className = 'entry-meta'; meta.textContent = [entry.category, (entry.record.labels || []).join(' · ')].filter(Boolean).join(' / ');
    button.append(title, preview, meta);
    button.onclick = async () => { if (await leave()) edit(entry); }; $('list').append(button);
  }
  if (!matches.length) {
    const empty = document.createElement('div'), title = document.createElement('strong'), hint = document.createElement('span');
    empty.className = 'empty-state';
    title.textContent = entries.length ? 'No matching experiences' : 'A place for what you learn';
    hint.textContent = entries.length ? 'Try another search or category.' : 'Choose your library, then add your first experience.';
    empty.append(title, hint); $('list').append(empty);
  }
}
function edit(entry) {
  selected = entry; mark(false); $('history-list').hidden = true; $('editor').hidden = false;
  $('notice').textContent = entry?.record.pending_revision ? 'An automatic revision suggestion exists. Saving here replaces it with your content.' : entry && entry.record.review?.decision !== 'accept' ? 'Suggestion: save to add this content to your usable library.' : '';
  $('notice').hidden = !$('notice').textContent;
  $('fields').replaceChildren();
  const guidance = document.createElement('section'), guidanceTitle = document.createElement('h3'), guidanceHelp = document.createElement('p');
  guidance.className = 'field-section'; guidanceTitle.textContent = 'Guidance';
  guidanceHelp.className = 'section-help'; guidanceHelp.textContent = 'When to use this experience, what to preserve, and how to check it.';
  guidance.append(guidanceTitle, guidanceHelp);
  const checks = document.createElement('div'); checks.className = 'field-grid';
  const metadata = document.createElement('details'), metadataTitle = document.createElement('summary'), metadataHelp = document.createElement('p'), metadataFields = document.createElement('div');
  metadata.className = 'metadata'; metadata.open = !entry; metadataTitle.textContent = 'Labels & mechanisms';
  metadataHelp.className = 'section-help'; metadataHelp.textContent = 'Check all items that apply. Choose at least one required mechanism.';
  metadataFields.className = 'field-grid'; metadata.append(metadataTitle, metadataHelp, metadataFields);
  for (const [key, title] of fields) {
    if (['labels', 'requires', 'excludes'].includes(key)) {
      const group = document.createElement('fieldset'), legend = document.createElement('legend'), optionsList = document.createElement('div');
      group.id = `field-${key}`; group.className = 'field choice-group'; legend.className = 'field-label'; legend.textContent = title;
      optionsList.className = 'choice-list'; group.append(legend, optionsList);
      const options = key === 'labels' ? (taxonomy.codebook || []).map(row => [row.code, `${row.code} · ${row.family}`]) : Object.keys(taxonomy.mechanism_predicates || {}).map(code => [code, code.replaceAll('_', ' ')]);
      const validate = () => {
        const first = optionsList.querySelector('input');
        if (key === 'requires' && first) first.setCustomValidity(optionsList.querySelector('input:checked') ? '' : 'Choose at least one required mechanism.');
      };
      for (const [code, text] of options) {
        const option = document.createElement('label'), checkbox = document.createElement('input'), caption = document.createElement('span');
        option.className = 'choice'; checkbox.type = 'checkbox'; checkbox.value = code; checkbox.checked = (entry?.record[key] || []).includes(code);
        caption.textContent = text; option.append(checkbox, caption); optionsList.append(option);
        checkbox.onchange = () => { validate(); mark(true); };
        checkbox.addEventListener('invalid', () => { metadata.open = true; });
      }
      validate(); metadataFields.append(group); continue;
    }
    const label = document.createElement('label'), caption = document.createElement('span');
    label.className = `field field-${key}`; caption.className = 'field-label'; caption.textContent = title;
    const symbol = {abstract: '▤', applicability: '✓', event_relation: '→'}[key];
    if (symbol) {
      const icon = document.createElement('span'); icon.className = 'field-icon'; icon.setAttribute('aria-hidden', 'true'); icon.textContent = symbol; caption.prepend(icon);
    }
    label.append(caption);
    if (key === 'abstract') {
      const help = document.createElement('span'); help.className = 'field-help';
      help.textContent = 'A short summary that helps retrieve this experience for a future task.'; label.append(help);
    }
    const input = document.createElement('textarea');
    const autoSize = ['title', 'abstract', 'applicability', 'event_relation'].includes(key);
    if (autoSize) { input.rows = 1; input.dataset.autosize = 'true'; }
    if (key === 'title') { caption.classList.add('sr-only'); input.placeholder = 'Experience title'; input.title = 'Edit experience title'; }
    input.id = `field-${key}`; input.required = true;
    input.value = (key === 'abstract' ? entry?.record.summary?.text : entry?.record[key]) || '';
    input.oninput = () => { mark(true); if (autoSize) fitField(input); };
    label.append(input);
    if (['title', 'abstract'].includes(key)) $('fields').append(label);
    else if (['preservation', 'exclusion'].includes(key)) checks.append(label);
    else {
      if (key === 'verification') guidance.append(checks);
      guidance.append(label);
    }
  }
  $('fields').append(guidance, metadata);
  if (entry) {
    const source = document.createElement('details'), title = document.createElement('summary'), body = document.createElement('pre');
    source.className = 'source-info'; title.textContent = 'Source information';
    body.textContent = JSON.stringify({id: entry.id, category: entry.category, file: entry.file, evidence: entry.record.evidence_ref || null, origin: entry.record.learning?.origin || null}, null, 2);
    source.append(title, body); $('fields').append(source);
  }
  $('delete').disabled = !entry; render();
  vscode.setState({id: entry?.id});
  requestAnimationFrame(fitAutoSizeFields);
}
let editorWidth;
new ResizeObserver(([entry]) => {
  if (entry.contentRect.width === editorWidth) return;
  editorWidth = entry.contentRect.width; fitAutoSizeFields();
}).observe($('fields'));
$('search').oninput = render; $('category').onchange = render;
$('new').onclick = async () => { if (await leave()) edit(null); };
for (const type of ['choose', 'reload', 'history']) $(type).onclick = async () => { if (await leave()) send(type); };
$('editor').onsubmit = event => {
  event.preventDefault(); if (busy) return;
  try {
    const record = {};
    for (const [key] of fields) record[key] = ['labels', 'requires', 'excludes'].includes(key) ? Array.from($(`field-${key}`).querySelectorAll('input:checked'), option => option.value) : $(`field-${key}`).value.trim();
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
    if (data.store) {
      $('store').textContent = data.store.split(/[\\/]/).filter(Boolean).slice(-2).join('/') || data.store;
      $('store').title = data.store;
    }
    const id = data.type === 'saved' ? data.id : selected?.id || vscode.getState()?.id;
    edit(entries.find(e => e.id === id) || entries[0] || null);
    message(data.type === 'saved' ? 'Saved. Future uses read the current content; existing run snapshots stay unchanged.' : `${entries.length} experiences`);
  } else if (data.type === 'select') { if (await leave()) edit(entries.find(e => e.id === data.id) || null); }
  else if (data.type === 'error') { setBusy(false); message(data.message, true); }
  else if (data.type === 'history') {
    $('editor').hidden = true; $('history-list').hidden = false; $('history-list').replaceChildren();
    const title = document.createElement('h2'), help = document.createElement('p');
    title.textContent = 'Library history'; help.className = 'section-help'; help.textContent = 'Select a saved version to inspect it. Save to restore its content.';
    $('history-list').append(title, help);
    for (const row of data.history.sort((a,b) => b.at.localeCompare(a.at))) {
      const button = document.createElement('button'), stamp = document.createElement('small'), title = document.createElement('span');
      button.className = 'history-row'; stamp.textContent = `${row.at} · ${row.action}`; title.textContent = row.record.title;
      button.append(stamp, title);
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
