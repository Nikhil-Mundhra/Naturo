// static/app.js
const el = id => document.getElementById(id);
const resultsList = el('results-list');
const previewImg = el('preview-img');
const placeholder = document.querySelector('.preview-placeholder');
const activeFilters = el('active-filters');
const materialSelect = el('material-select');
const colorSelect = el('color-select');

function showDebug(obj) {
  const dbg = el('debug-panel');
  const pre = el('debug-json');
  dbg.hidden = false;
  pre.textContent = JSON.stringify(obj, null, 2);
}

// populate material & color from server-side constants (quick: inline map)
const MATERIALS = ["", "PVC", "WPC", "Charcoal", "Acrylic"]; // add more as desired
const COLORS = ["", "Black", "White", "Gold", "Silver", "Beage", "Blue"];

function makeOptions(sel, arr) {
  sel.innerHTML = '';
  arr.forEach(x => {
    const o = document.createElement('option'); o.value = x; o.textContent = x;
    sel.appendChild(o);
  });
}
makeOptions(materialSelect, MATERIALS);
makeOptions(colorSelect, COLORS);

document.getElementById('search-code-btn').onclick = async () => {
  const code = el('code-input').value.trim();
  if (!code) return alert('Please enter a product code.');
  activeFilters.textContent = `Product code: ${code}`;
  resultsList.innerHTML = '<div class="meta">Searching…</div>';
  const resp = await fetch('/api/search_code', {
    method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({code})
  });
  const j = await resp.json();
  if (j.error) {
    resultsList.innerHTML = `<div class="meta">Error: ${j.error}</div>`;
    showDebug(j);
    return;
  }
  renderResults(j.matches, j.debug);
};

document.getElementById('search-qn-btn').onclick = async () => {
  const material = materialSelect.value || null;
  const color = colorSelect.value || null;
  const height = el('height-select').value || null;
  const width = el('width-input').value || null;

  const selection = {
    material: material ? [material.toLowerCase()] : [],
    color: color ? [color.toLowerCase()] : [],
    size: [],
    designs: [],
    supplier: null,
    folder_code: null,
    file_token: null
  };
  if (height) selection.size.push(height);
  if (width) selection.size.push(width.endsWith('"') ? width : `${width}"`);

  activeFilters.textContent = [
    material && `Material: ${material}`,
    color && `Color: ${color}`,
    height && `Height: ${height}`,
    width && `Width: ${width}`
  ].filter(Boolean).join(' | ') || 'No filters applied';

  resultsList.innerHTML = '<div class="meta">Searching…</div>';
  const resp = await fetch('/api/search_qn', {
    method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({selection})
  });
  const j = await resp.json();
  if (j.error) {
    resultsList.innerHTML = `<div class="meta">Error: ${j.error}</div>`;
    showDebug(j);
    return;
  }
  // Combine exact + suggestions for listing (tag suggestions)
  const items = (j.exact || []).map(p => ({path:p, tag:null}))
    .concat((j.suggestions || []).map(s => ({path:s[0], tag:`missing:${s[1].join(',')};score:${s[2]}`})));
  renderResults(items.map(it => it.path), j.debug);
};

async function renderResults(list, debug) {
  resultsList.innerHTML = '';
  if (!list || list.length === 0) {
    resultsList.innerHTML = '<div class="meta">No results</div>';
    return;
  }
  list.forEach((p, idx) => {
    const div = document.createElement('div');
    div.className = 'result-item';
    div.dataset.path = p;
    const name = document.createElement('div');
    name.textContent = p.split('/').slice(-1)[0];
    const meta = document.createElement('div');
    meta.className = 'meta';
    meta.textContent = p.split('/').slice(0,-1).join('/') || '/';
    div.appendChild(name);
    div.appendChild(meta);
    div.onclick = () => selectResult(div);
    resultsList.appendChild(div);
    if (idx===0) div.classList.add('selected'), selectResult(div);
  });
  if (debug) showDebug(debug);
}

let currentSelected = null;
async function selectResult(itemDiv) {
  if (currentSelected) currentSelected.classList.remove('selected');
  itemDiv.classList.add('selected');
  currentSelected = itemDiv;
  const p = itemDiv.dataset.path;
  placeholder.style.display = 'none';
  previewImg.style.display = 'none';
  // fetch thumbnail
  const resp = await fetch(`/api/thumbnail?path=${encodeURIComponent(p)}`);
  const j = await resp.json();
  if (j.error) {
    placeholder.style.display = 'block';
    placeholder.textContent = 'Preview not available';
    return;
  }
  previewImg.src = j.data;
  previewImg.style.display = 'block';
}

// refresh index
document.getElementById('refresh-btn').onclick = async () => {
  const resp = await fetch('/api/refresh_index', {method:'POST'});
  const j = await resp.json();
  if (j.ok) alert('Index refreshed');
  else alert('Refresh failed: ' + (j.error || 'unknown'));
};
