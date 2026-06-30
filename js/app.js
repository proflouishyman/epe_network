// EPE Network — app.js

// ── FORM URLS ─────────────────────────────────────────────
// Replace these with real Google Forms URLs after creating the forms.
const FORM_URL_CENTER     = 'https://docs.google.com/forms/d/e/1FAIpQLSci_-chUcEJ8zRdVWyyek97IaOtf4I611DxgbxRu9hbSMZCvQ/viewform';
const FORM_URL_INDIVIDUAL = 'https://docs.google.com/forms/d/e/1FAIpQLSckdC5YvPYTOyeQ9T4aT-O_3hA1YWgbjM-45rCbX-_HFMH0mQ/viewform';

let centers = [];
let individuals = [];
let topicTaxonomy = [];  // [{id, label, group}]
let activeRegionFilter = null;

async function loadData() {
  try {
    const [cRes, iRes, tRes] = await Promise.all([
      fetch('data/centers.json'),
      fetch('data/individuals.json'),
      fetch('data/topics.json'),
    ]);
    centers     = await cRes.json();
    individuals = await iRes.json();
    topicTaxonomy = await tRes.json();
  } catch (e) {
    console.error('Could not load data:', e);
  }
  init();
}

function init() {
  updateStats();
  buildRegionFilters();
  buildCentersGrid();
  buildScholarFilters();
  buildScholarsView();
  buildTopicsCloud();
  setupEventListeners();
  handleHash();
}

// Open the right modal if the page loaded with a deep-link hash.
function handleHash() {
  const hash = decodeURIComponent(window.location.hash.slice(1));
  if (!hash) return;
  const [type, id] = hash.split('/');
  if (type === 'center' && id) openCenterModal(id);
  if (type === 'scholar' && id) {
    // Switch to scholars tab so the context is right
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById('scholars-view').classList.add('active');
    document.querySelectorAll('.nav-tab').forEach(t =>
      t.classList.toggle('active', t.dataset.tab === 'scholars'));
    openScholarModal(id);
  }
}

function updateStats() {
  const countries = new Set(centers.map(c => c.country));
  document.getElementById('stat-centers').textContent = centers.length;
  document.getElementById('stat-countries').textContent = countries.size;
}

// ── HELPERS ───────────────────────────────────────────────

const REGION_COLORS = {
  'North America':        { bg: '#E8EEF8', color: '#1C3A6E' },
  'Europe':               { bg: '#EBE8F4', color: '#3D2B70' },
  'Latin America':        { bg: '#FCF0E6', color: '#7A3A1A' },
  'Africa':               { bg: '#E8F4EB', color: '#1E5A2A' },
  'South/Southeast Asia': { bg: '#FBF4DC', color: '#5A4200' },
  'MENA':                 { bg: '#F4EFE5', color: '#5A3A18' },
};

// Builds two side-by-side QR codes for a modal.
// shareUrl: deep link to this profile page. formUrl: registration/update form.
function qrSection(shareUrl, formUrl, formLabel) {
  const encode = url => encodeURIComponent(url);
  const api = (url, size = 140) =>
    `https://api.qrserver.com/v1/create-qr-code/?size=${size}x${size}&margin=6&data=${encode(url)}`;
  return `
    <div class="qr-section">
      <div class="qr-item">
        <img class="qr-img" src="${api(shareUrl)}" alt="QR code — share profile" loading="lazy" width="140" height="140">
        <div class="qr-label">Share this profile</div>
        <a class="qr-link" href="${escAttr(shareUrl)}">${escHtml(shareUrl)}</a>
      </div>
      <div class="qr-item">
        <img class="qr-img" src="${api(formUrl)}" alt="QR code — ${escAttr(formLabel)}" loading="lazy" width="140" height="140">
        <div class="qr-label">${escHtml(formLabel)}</div>
        <a class="qr-link" href="${escAttr(formUrl)}" target="_blank" rel="noopener">Open form ↗</a>
      </div>
    </div>
  `;
}

// Deep-link URL for a center or scholar.
function profileUrl(type, id) {
  return `${window.location.origin}${window.location.pathname}#${type}/${encodeURIComponent(id)}`;
}

// Returns an <img> if logo_url is set, otherwise a styled monogram badge.
function logoBadge(c, size = 42) {
  if (c.logo_url) {
    return `<img class="logo-img" src="${escAttr(c.logo_url)}" alt="${escAttr(c.name)}" width="${size}" height="${size}" loading="lazy">`;
  }
  const { bg, color } = REGION_COLORS[c.region] || { bg: '#EEE', color: '#555' };
  const words = c.name.replace(/[()[\]]/g, '').split(/[\s&,/]+/)
    .filter(w => w.length > 2 && !['the','and','for','of','at','in','on','an','a'].includes(w.toLowerCase()));
  const initials = words.length >= 2
    ? (words[0][0] + words[1][0]).toUpperCase()
    : c.name.slice(0, 2).toUpperCase();
  return `<div class="logo-badge" style="width:${size}px;height:${size}px;min-width:${size}px;background:${bg};color:${color}">${initials}</div>`;
}

// "Baltimore, MD · United States"  or  "São Paulo · Brazil"
function locationStr(c) {
  const city = c.city || '';
  const state = c.state || '';
  const country = c.country || '';
  const local = state ? `${city}, ${state}` : city;
  return [local, country].filter(Boolean).join(' · ');
}

// Tags for a center: use topic arrays if populated, else fall back to focus_areas.
function centerTopicTags(c, maxTotal = 5) {
  const current   = (c.topics_current   || []).map(t => `<span class="tag current">${escHtml(t)}</span>`);
  const antici    = (c.topics_anticipated|| []).map(t => `<span class="tag anticipated">${escHtml(t)}</span>`);
  const wouldLike = (c.topics_would_like || []).map(t => `<span class="tag would-like">${escHtml(t)}</span>`);
  const all = [...current, ...antici, ...wouldLike];
  if (all.length) return all.slice(0, maxTotal).join('');
  return (c.focus_areas || []).slice(0, maxTotal).map(t => `<span class="tag">${escHtml(t)}</span>`).join('');
}

// ── CENTERS ──────────────────────────────────────────────

function buildRegionFilters() {
  const regions = [...new Set(centers.map(c => c.region).filter(Boolean))].sort();
  const container = document.getElementById('region-filter-chips');
  container.innerHTML = '';
  container.appendChild(makeChip('All Regions', true, () => setRegionFilter(null)));
  regions.forEach(r => container.appendChild(makeChip(r, false, () => setRegionFilter(r))));
}

function makeChip(label, active, onClick) {
  const btn = document.createElement('button');
  btn.className = 'chip' + (active ? ' active' : '');
  btn.textContent = label;
  btn.addEventListener('click', () => {
    document.querySelectorAll('#region-filter-chips .chip').forEach(c => c.classList.remove('active'));
    btn.classList.add('active');
    onClick();
  });
  return btn;
}

function setRegionFilter(region) {
  activeRegionFilter = region;
  buildCentersGrid(document.getElementById('center-search').value);
}

function buildCentersGrid(search = '') {
  const q = search.toLowerCase();
  let filtered = centers;
  if (activeRegionFilter) filtered = filtered.filter(c => c.region === activeRegionFilter);
  if (q) filtered = filtered.filter(c =>
    c.name.toLowerCase().includes(q) ||
    (c.institution || '').toLowerCase().includes(q) ||
    (c.country || '').toLowerCase().includes(q) ||
    (c.city || '').toLowerCase().includes(q) ||
    (c.director || '').toLowerCase().includes(q) ||
    (c.focus_areas || []).some(t => t.toLowerCase().includes(q)) ||
    (c.topics_current || []).some(t => t.toLowerCase().includes(q)) ||
    (c.topics_would_like || []).some(t => t.toLowerCase().includes(q))
  );

  document.getElementById('centers-count').textContent =
    `${filtered.length} center${filtered.length !== 1 ? 's' : ''}`;

  const grid = document.getElementById('centers-grid');
  if (!filtered.length) {
    grid.innerHTML = '<div class="empty-state"><p>No centers match your search.</p></div>';
    return;
  }

  grid.innerHTML = filtered.map(c => `
    <div class="center-card" data-id="${escAttr(c.id)}" role="button" tabindex="0"
         aria-label="View details for ${escAttr(c.name)}">
      <div class="center-card-location">
        <span>${c.flag || ''}</span>
        <span>${escHtml(locationStr(c))}</span>
      </div>
      <div class="center-card-header">
        ${logoBadge(c, 42)}
        <div class="center-card-name-wrap">
          <div class="center-card-name">${escHtml(c.name)}</div>
          <div class="center-card-institution">${escHtml(c.institution || '')}</div>
        </div>
      </div>
      ${c.director ? `<div class="center-card-director">Dir. <strong>${escHtml(c.director)}</strong></div>` : ''}
      ${c.contact  ? `<div class="center-card-contact"><a href="mailto:${escAttr(c.contact)}" onclick="event.stopPropagation()">${escHtml(c.contact)}</a></div>` : ''}
      <div class="tags">${centerTopicTags(c)}</div>
    </div>
  `).join('');

  grid.querySelectorAll('.center-card').forEach(card => {
    card.addEventListener('click', () => openCenterModal(card.dataset.id));
    card.addEventListener('keydown', e => { if (e.key === 'Enter') openCenterModal(card.dataset.id); });
  });
}

function openCenterModal(id) {
  const c = centers.find(x => x.id === id);
  if (!c) return;
  const members = individuals.filter(i => i.center_id === id);

  const hasTopics = (c.topics_current||[]).length + (c.topics_anticipated||[]).length + (c.topics_would_like||[]).length > 0;

  document.getElementById('center-modal-body').innerHTML = `
    <div class="modal-header-row">
      <div class="modal-header-text">
        <div class="modal-location">${escHtml(c.region || '')} · ${escHtml(locationStr(c))}</div>
        <div class="modal-name" id="center-modal-title">${escHtml(c.name)}</div>
        <div class="modal-institution">${escHtml(c.institution || '')}</div>
        ${c.website ? `<a class="modal-link" href="${escAttr(c.website)}" target="_blank" rel="noopener">${escHtml(c.website)}</a>` : ''}
      </div>
      ${logoBadge(c, 56)}
    </div>
    <hr class="modal-divider">
    ${c.director ? section('Director', escHtml(c.director)) : ''}
    ${c.contact  ? section('Contact',  `<a class="modal-link" href="mailto:${escAttr(c.contact)}">${escHtml(c.contact)}</a>`) : ''}
    ${c.year_established ? section('Established', escHtml(String(c.year_established))) : ''}
    <hr class="modal-divider">
    ${hasTopics ? `
      ${c.topics_current?.length    ? section('Current Research',
          `<div class="tags">${c.topics_current.map(t    => `<span class="tag current">${escHtml(t)}</span>`).join('')}</div>`) : ''}
      ${c.topics_anticipated?.length ? section('Anticipated Research',
          `<div class="tags">${c.topics_anticipated.map(t => `<span class="tag anticipated">${escHtml(t)}</span>`).join('')}</div>`) : ''}
      ${c.topics_would_like?.length  ? section('Would Like to Work On',
          `<div class="tags">${c.topics_would_like.map(t  => `<span class="tag would-like">${escHtml(t)}</span>`).join('')}</div>`) : ''}
      ${c.focus_areas?.length ? section('Research Profile',
          `<div class="tags">${c.focus_areas.map(t => `<span class="tag">${escHtml(t)}</span>`).join('')}</div>`) : ''}
    ` : `
      ${c.focus_areas?.length ? section('Research Profile',
          `<div class="tags">${c.focus_areas.map(t => `<span class="tag">${escHtml(t)}</span>`).join('')}</div>`) : ''}
    `}
    ${c.current_projects  ? section('Current Projects',  escHtml(c.current_projects)) : ''}
    ${c.funding_sources   ? section('Funding',           escHtml(c.funding_sources))  : ''}
    ${c.connected_networks?.length ? section('Connected Networks', escHtml(c.connected_networks.join(', '))) : ''}
    ${(c.problems || c.opportunities) ? '<hr class="modal-divider">' : ''}
    ${c.problems     ? section('Challenges',    escHtml(c.problems))     : ''}
    ${c.opportunities ? section('Opportunities', escHtml(c.opportunities)) : ''}
    ${members.length ? `
      <hr class="modal-divider">
      ${section(`Affiliated Scholars (${members.length})`,
        members.map(s => `
          <div class="topic-item" data-scholar-id="${escAttr(s.id)}">
            <div class="topic-item-name">${escHtml(s.name)}</div>
            <div class="topic-item-sub">${escHtml([s.title, s.institution].filter(Boolean).join(' · '))}</div>
          </div>
        `).join('')
      )}
    ` : ''}
    <hr class="modal-divider">
    ${qrSection(profileUrl('center', c.id), FORM_URL_CENTER, 'Register / update this center')}
  `;

  document.getElementById('center-modal-body').querySelectorAll('[data-scholar-id]').forEach(el => {
    el.addEventListener('click', () => { closeCenterModal(); openScholarModal(el.dataset.scholarId); });
  });

  history.replaceState(null, '', `#center/${encodeURIComponent(c.id)}`);
  openModal('center-modal');
}

function closeCenterModal() {
  closeModal('center-modal');
  history.replaceState(null, '', window.location.pathname);
}

// ── SCHOLARS ─────────────────────────────────────────────

function buildScholarFilters() {
  const centerSel = document.getElementById('center-filter');
  const regionSel = document.getElementById('region-filter');
  const topicSel  = document.getElementById('topic-filter');

  [...centers].sort((a, b) => a.name.localeCompare(b.name)).forEach(c => {
    addOption(centerSel, c.id, c.name);
  });

  [...new Set(individuals.map(i => i.region).filter(Boolean))].sort().forEach(r => {
    addOption(regionSel, r, r);
  });

  // Build topic dropdown grouped by taxonomy category
  const usedLabels = new Set(individuals.flatMap(i => [
    ...(i.topics_current || []),
    ...(i.topics_anticipated || []),
    ...(i.topics_would_like || []),
  ]));

  // Group taxonomy by group, preserving order
  const groups = new Map();
  for (const t of topicTaxonomy) {
    if (!groups.has(t.group)) groups.set(t.group, []);
    groups.get(t.group).push(t);
  }

  for (const [groupName, topics] of groups) {
    const optgroup = document.createElement('optgroup');
    optgroup.label = groupName;
    let anyUsed = false;
    for (const t of topics) {
      if (usedLabels.has(t.label)) {
        addOption(optgroup, t.label, t.label);
        anyUsed = true;
      }
    }
    if (anyUsed) topicSel.appendChild(optgroup);
  }

  // Append any free-text topics not in taxonomy (from old form submissions)
  const taxonomyLabels = new Set(topicTaxonomy.map(t => t.label));
  const freeText = [...usedLabels].filter(l => !taxonomyLabels.has(l)).sort();
  if (freeText.length) {
    const og = document.createElement('optgroup');
    og.label = 'Other';
    freeText.forEach(t => addOption(og, t, t));
    topicSel.appendChild(og);
  }
}

function addOption(parent, value, text) {
  const opt = document.createElement('option');
  opt.value = value;
  opt.textContent = text;
  parent.appendChild(opt);
}

// Returns the last-name token used for alphabetical sorting and indexing.
function scholarSortKey(name) {
  const parts = name.trim().split(/\s+/);
  return parts[parts.length - 1].normalize('NFD').replace(/[̀-ͯ]/g, '').toUpperCase();
}

function buildScholarsView() {
  const q        = document.getElementById('scholar-search').value.toLowerCase();
  const centerId = document.getElementById('center-filter').value;
  const region   = document.getElementById('region-filter').value;
  const topic    = document.getElementById('topic-filter').value;

  let filtered = individuals;
  if (centerId) filtered = filtered.filter(i => i.center_id === centerId);
  if (region)   filtered = filtered.filter(i => i.region === region);
  if (topic)    filtered = filtered.filter(i =>
    [...(i.topics_current||[]), ...(i.topics_anticipated||[]), ...(i.topics_would_like||[])].includes(topic)
  );
  if (q) filtered = filtered.filter(i =>
    i.name.toLowerCase().includes(q) ||
    (i.institution || '').toLowerCase().includes(q) ||
    (i.topics_current || []).some(t => t.toLowerCase().includes(q)) ||
    (i.topics_would_like || []).some(t => t.toLowerCase().includes(q))
  );

  // Sort alphabetically by last name
  filtered = [...filtered].sort((a, b) => scholarSortKey(a.name).localeCompare(scholarSortKey(b.name)));

  document.getElementById('scholars-count').textContent =
    `${filtered.length} scholar${filtered.length !== 1 ? 's' : ''}`;

  const list = document.getElementById('scholars-list');
  if (!filtered.length) {
    list.innerHTML = '<div class="empty-state"><p>No scholars match your filters.</p></div>';
    renderAlphaIndex([], list);
    return;
  }

  // Group by first letter of last name
  const groups = new Map();
  for (const i of filtered) {
    const letter = scholarSortKey(i.name)[0] || '#';
    if (!groups.has(letter)) groups.set(letter, []);
    groups.get(letter).push(i);
  }

  // Build letter index bar
  renderAlphaIndex([...groups.keys()], list);

  // Render grouped rows
  let html = '';
  for (const [letter, scholars] of groups) {
    html += `<div class="alpha-section-head" id="alpha-${letter}">${letter}</div>`;
    html += scholars.map(i => {
      const center = centers.find(c => c.id === i.center_id);
      const topicTags = [
        ...(i.topics_current    || []).map(t => `<span class="tag current">${escHtml(t)}</span>`),
        ...(i.topics_would_like || []).map(t => `<span class="tag would-like">${escHtml(t)}</span>`),
      ];
      return `
        <div class="scholar-row" data-id="${escAttr(i.id)}" role="button" tabindex="0">
          <div>
            <div class="scholar-name">${escHtml(i.name)}</div>
            <div class="scholar-meta">${escHtml([i.title, i.institution].filter(Boolean).join(' · '))}</div>
            ${center ? `<div class="scholar-center">${escHtml(center.name)}</div>` : ''}
          </div>
          <div class="scholar-topics">${topicTags.slice(0, 6).join('')}</div>
          <div class="scholar-country">${escHtml(i.country || '')}</div>
        </div>
      `;
    }).join('');
  }
  list.innerHTML = html;

  list.querySelectorAll('.scholar-row').forEach(row => {
    row.addEventListener('click', () => openScholarModal(row.dataset.id));
    row.addEventListener('keydown', e => { if (e.key === 'Enter') openScholarModal(row.dataset.id); });
  });
}

function renderAlphaIndex(activeLetters, listEl) {
  const existing = document.getElementById('alpha-index');
  if (existing) existing.remove();

  const activeSet = new Set(activeLetters);
  const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');

  const bar = document.createElement('div');
  bar.id = 'alpha-index';
  bar.className = 'alpha-index';
  bar.innerHTML = LETTERS.map(l => {
    if (activeSet.has(l)) {
      return `<a class="alpha-btn alpha-btn--active" href="#alpha-${l}">${l}</a>`;
    }
    return `<span class="alpha-btn alpha-btn--empty">${l}</span>`;
  }).join('');

  listEl.parentElement.insertBefore(bar, listEl);
}

function openScholarModal(id) {
  const s = individuals.find(x => x.id === id);
  if (!s) return;
  const center = centers.find(c => c.id === s.center_id);

  document.getElementById('scholar-modal-body').innerHTML = `
    <div class="modal-location">${escHtml(s.country || '')}</div>
    <div class="modal-name" id="scholar-modal-title">${escHtml(s.name)}</div>
    <div class="modal-institution">
      ${escHtml([s.title, s.institution].filter(Boolean).join(' · '))}
      ${center ? ` · <span style="color:var(--terracotta);font-weight:700">${escHtml(center.name)}</span>` : ''}
    </div>
    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:4px">
      ${s.email   ? `<a class="modal-link" href="mailto:${escAttr(s.email)}">${escHtml(s.email)}</a>` : ''}
      ${s.website ? `<a class="modal-link" href="${escAttr(s.website)}" target="_blank" rel="noopener">${escHtml(s.website)}</a>` : ''}
    </div>
    <hr class="modal-divider">
    ${s.topics_current?.length     ? section('Current Research',
        `<div class="tags">${s.topics_current.map(t    => `<span class="tag current">${escHtml(t)}</span>`).join('')}</div>`) : ''}
    ${s.topics_anticipated?.length  ? section('Anticipated Research',
        `<div class="tags">${s.topics_anticipated.map(t => `<span class="tag anticipated">${escHtml(t)}</span>`).join('')}</div>`) : ''}
    ${s.topics_would_like?.length   ? section('Would Like to Work On',
        `<div class="tags">${s.topics_would_like.map(t  => `<span class="tag would-like">${escHtml(t)}</span>`).join('')}</div>`) : ''}
    ${s.teaching_regions?.length    ? section('Teaching — Regional Focus',  escHtml(s.teaching_regions.join(', '))) : ''}
    ${s.teaching_levels?.length     ? section('Teaching — Level',           escHtml(s.teaching_levels.join(', ')))  : ''}
    ${s.connected_networks?.length  ? section('Connected Networks',         escHtml(s.connected_networks.join(', '))) : ''}
    ${(s.problems || s.opportunities) ? '<hr class="modal-divider">' : ''}
    ${s.problems     ? section('Challenges',    escHtml(s.problems))     : ''}
    ${s.opportunities ? section('Opportunities', escHtml(s.opportunities)) : ''}
    <hr class="modal-divider">
    ${qrSection(profileUrl('scholar', s.id), FORM_URL_INDIVIDUAL, 'Register / update your profile')}
  `;

  history.replaceState(null, '', `#scholar/${encodeURIComponent(s.id)}`);
  openModal('scholar-modal');
}

function closeScholarModal() {
  closeModal('scholar-modal');
  history.replaceState(null, '', window.location.pathname);
}

// ── TOPICS ────────────────────────────────────────────────

function buildTopicsCloud() {
  const counts = {};

  // Center contributions: focus_areas get +2, topic arrays +1 each
  centers.forEach(c => {
    (c.focus_areas         || []).forEach(t => { counts[t] = (counts[t]||0) + 2; });
    (c.topics_current      || []).forEach(t => { counts[t] = (counts[t]||0) + 2; });
    (c.topics_anticipated  || []).forEach(t => { counts[t] = (counts[t]||0) + 1; });
    (c.topics_would_like   || []).forEach(t => { counts[t] = (counts[t]||0) + 1; });
  });

  // Individual contributions
  individuals.forEach(i => {
    [...(i.topics_current||[]), ...(i.topics_anticipated||[]), ...(i.topics_would_like||[])]
      .forEach(t => { counts[t] = (counts[t]||0) + 1; });
  });

  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const max = sorted[0]?.[1] || 1;
  const min = sorted[sorted.length-1]?.[1] || 1;

  const cloud = document.getElementById('topics-cloud');
  cloud.innerHTML = sorted.map(([topic, count]) => {
    const size = 14 + Math.round(((count - min) / ((max - min) || 1)) * 14);
    return `<button class="topic-pill" data-topic="${escAttr(topic)}" style="font-size:${size}px">${escHtml(topic)}</button>`;
  }).join('');

  cloud.querySelectorAll('.topic-pill').forEach(pill => {
    pill.addEventListener('click', () => showTopicResults(pill.dataset.topic));
  });
}

function showTopicResults(topic) {
  document.querySelectorAll('.topic-pill').forEach(p =>
    p.classList.toggle('active', p.dataset.topic === topic)
  );
  document.getElementById('topics-cloud').style.display = 'none';
  document.getElementById('topics-intro').style.display = 'none';
  document.getElementById('topic-results').classList.remove('hidden');
  document.getElementById('topic-title').textContent = topic;

  // A center matches if topic appears in any of its topic arrays or focus_areas
  const relCenters = centers.filter(c =>
    (c.focus_areas        ||[]).includes(topic) ||
    (c.topics_current     ||[]).includes(topic) ||
    (c.topics_anticipated ||[]).includes(topic) ||
    (c.topics_would_like  ||[]).includes(topic)
  );

  const relScholars = individuals.filter(i =>
    [...(i.topics_current||[]), ...(i.topics_anticipated||[]), ...(i.topics_would_like||[])].includes(topic)
  );

  const centersEl = document.getElementById('topic-centers');
  centersEl.innerHTML = relCenters.length
    ? relCenters.map(c => {
        const isCurrent    = (c.topics_current    ||[]).includes(topic);
        const isAnticipated = (c.topics_anticipated||[]).includes(topic);
        const isWouldLike  = (c.topics_would_like ||[]).includes(topic);
        const badge = isCurrent
          ? '<span class="topic-item-badge badge-current">current</span>'
          : isAnticipated
          ? '<span class="topic-item-badge badge-anticipated">anticipated</span>'
          : isWouldLike
          ? '<span class="topic-item-badge badge-would-like">would like</span>'
          : '';
        return `
          <div class="topic-item" data-center-id="${escAttr(c.id)}">
            <div class="topic-item-name">${escHtml(c.name)}${badge}</div>
            <div class="topic-item-sub">${escHtml([c.institution, locationStr(c)].filter(Boolean).join(' · '))}</div>
          </div>
        `;
      }).join('')
    : '<p style="color:var(--charcoal-soft);font-style:italic;font-size:13px">No centers listed.</p>';

  const scholarsEl = document.getElementById('topic-scholars');
  scholarsEl.innerHTML = relScholars.length
    ? relScholars.map(s => {
        const isCurrent   = (s.topics_current   ||[]).includes(topic);
        const isWouldLike = (s.topics_would_like||[]).includes(topic);
        const badge = isCurrent
          ? '<span class="topic-item-badge badge-current">current</span>'
          : isWouldLike
          ? '<span class="topic-item-badge badge-would-like">would like</span>'
          : '';
        return `
          <div class="topic-item" data-scholar-id="${escAttr(s.id)}">
            <div class="topic-item-name">${escHtml(s.name)}${badge}</div>
            <div class="topic-item-sub">${escHtml([s.institution, s.country].filter(Boolean).join(' · '))}</div>
          </div>
        `;
      }).join('')
    : '<p style="color:var(--charcoal-soft);font-style:italic;font-size:13px">No scholars listed.</p>';

  centersEl.querySelectorAll('[data-center-id]').forEach(el =>
    el.addEventListener('click', () => openCenterModal(el.dataset.centerId))
  );
  scholarsEl.querySelectorAll('[data-scholar-id]').forEach(el =>
    el.addEventListener('click', () => openScholarModal(el.dataset.scholarId))
  );
}

function hideTopicResults() {
  document.querySelectorAll('.topic-pill').forEach(p => p.classList.remove('active'));
  document.getElementById('topics-cloud').style.display = '';
  document.getElementById('topics-intro').style.display = '';
  document.getElementById('topic-results').classList.add('hidden');
}

// ── MODAL HELPERS ─────────────────────────────────────────

function openModal(id) {
  document.getElementById(id).classList.remove('hidden');
  document.body.style.overflow = 'hidden';
}

function closeModal(id) {
  document.getElementById(id).classList.add('hidden');
  document.body.style.overflow = '';
}

function section(label, content) {
  return `
    <div class="modal-section">
      <div class="modal-section-label">${label}</div>
      <div class="modal-section-content">${content}</div>
    </div>
  `;
}

// ── ESCAPE HELPERS ────────────────────────────────────────

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function escAttr(str) {
  return String(str).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

// ── EVENT LISTENERS ───────────────────────────────────────

function setupEventListeners() {
  document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById(`${tab.dataset.tab}-view`).classList.add('active');
    });
  });

  document.getElementById('center-search').addEventListener('input', e =>
    buildCentersGrid(e.target.value)
  );

  ['scholar-search', 'center-filter', 'region-filter', 'topic-filter'].forEach(id => {
    const el = document.getElementById(id);
    el.addEventListener('input',  buildScholarsView);
    el.addEventListener('change', buildScholarsView);
  });

  document.getElementById('center-modal-close')   .addEventListener('click', closeCenterModal);
  document.getElementById('center-modal-backdrop').addEventListener('click', closeCenterModal);
  document.getElementById('scholar-modal-close')   .addEventListener('click', closeScholarModal);
  document.getElementById('scholar-modal-backdrop').addEventListener('click', closeScholarModal);

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { closeCenterModal(); closeScholarModal(); }
  });

  document.getElementById('topic-back').addEventListener('click', hideTopicResults);
}

// ── START ─────────────────────────────────────────────────

loadData();
