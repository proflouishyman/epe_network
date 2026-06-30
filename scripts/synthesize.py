#!/usr/bin/env python3
"""
synthesize.py — Convert Google Forms CSV exports into JSON for the EPE Network site.

Usage:
  1. From Google Sheets: File → Download → CSV (place files in data/)
     - Centers form responses  → data/centers_responses.csv
     - Individuals form responses → data/individuals_responses.csv
  2. Run: python3 scripts/synthesize.py
  3. Commit the updated data/centers.json and data/individuals.json to GitHub.

Deduplication: if the same center (by name) or scholar (by email) submits more
than once, the LATEST submission wins. Older entries are discarded.
"""

import csv
import json
import re
import sys
from pathlib import Path
from datetime import datetime

# ── CONFIGURATION ─────────────────────────────────────────────────────────────
# These values must match your Google Form field labels EXACTLY.
# If you rename a question, update the string here too.

CENTER_COLUMNS = {
    'timestamp':            'Timestamp',
    'name':                 'Center Name',
    'institution':          'Institution / University',
    'city':                 'City',
    'state':                'State / Province (if applicable)',
    'country':              'Country',
    'website':              'Website URL',
    'logo_url':             'Logo Image URL (optional)',
    'director':             'Director / Primary Contact Name',
    'contact':              'Contact Email',
    'year_established':     'Year Established',
    # Checkbox groups all have the same label; deduplicated as _2, _3
    'topics_current':            'Select all that apply',
    'topics_current_text':       'Additional current topics not listed above',
    'topics_anticipated':        'Select all that apply_2',
    'topics_anticipated_text':   'Additional anticipated topics not listed above',
    'topics_would_like':         'Select all that apply_3',
    'topics_would_like_text':    'Additional "would like" topics not listed above',
    'focus_areas':          'Thematic Focus Areas (general profile)',
    'current_projects':     'Current Research Projects',
    'funding_sources':      'Funding Sources',
    'problems':             'Organizational Challenges / Problems',
    'opportunities':        'Opportunities (offering or seeking)',
    'connected_networks':   'Connected External Networks & Meetings',
    'notes':                'Anything else you would like to share',
}

INDIVIDUAL_COLUMNS = {
    'timestamp':           'Timestamp',
    'name':                'Full Name',
    'title':               'Title / Position',
    'center_name':         'Center Affiliation',
    'institution':         'Institution',
    'country':             'Country',
    'email':               'Email',
    'website':             'Personal / Academic Website',
    # Checkbox groups all have the same label; deduplicated as _2, _3
    'topics_current':      'Select all that apply',
    'topics_current_text': 'Additional current topics not listed above',
    'topics_anticipated':  'Select all that apply_2',
    'topics_anticipated_text': 'Additional anticipated topics not listed above',
    'topics_would_like':   'Select all that apply_3',
    'topics_would_like_text':  'Additional "would like" topics not listed above',
    'teaching_regions':    'Teaching – Regional Focus',
    'teaching_levels':     'Teaching – Level',
    'connected_networks':  'Connected External Networks & Meetings',
    'problems':            'Problems (research, funding, organizational)',
    'opportunities':       'Opportunities (offering or seeking)',
    'notes':               'Anything else you would like to share',
}

COUNTRY_TO_REGION = {
    'United States': 'North America', 'Canada': 'North America',
    'Mexico': 'Latin America', 'Brazil': 'Latin America', 'Argentina': 'Latin America',
    'Chile': 'Latin America', 'Colombia': 'Latin America', 'Peru': 'Latin America',
    'Venezuela': 'Latin America', 'Ecuador': 'Latin America', 'Bolivia': 'Latin America',
    'United Kingdom': 'Europe', 'Germany': 'Europe', 'France': 'Europe',
    'Italy': 'Europe', 'Spain': 'Europe', 'Netherlands': 'Europe', 'Sweden': 'Europe',
    'Norway': 'Europe', 'Denmark': 'Europe', 'Finland': 'Europe', 'Switzerland': 'Europe',
    'Austria': 'Europe', 'Belgium': 'Europe', 'Portugal': 'Europe', 'Poland': 'Europe',
    'Greece': 'Europe', 'Czech Republic': 'Europe', 'Hungary': 'Europe',
    'South Africa': 'Africa', 'Nigeria': 'Africa', 'Kenya': 'Africa', 'Ghana': 'Africa',
    'Ethiopia': 'Africa', 'Tanzania': 'Africa', 'Uganda': 'Africa', 'Senegal': 'Africa',
    'Cameroon': 'Africa', 'Côte d\'Ivoire': 'Africa', 'Mozambique': 'Africa',
    'India': 'South/Southeast Asia', 'Pakistan': 'South/Southeast Asia',
    'Bangladesh': 'South/Southeast Asia', 'Indonesia': 'South/Southeast Asia',
    'Thailand': 'South/Southeast Asia', 'Vietnam': 'South/Southeast Asia',
    'Philippines': 'South/Southeast Asia', 'Malaysia': 'South/Southeast Asia',
    'Sri Lanka': 'South/Southeast Asia', 'Myanmar': 'South/Southeast Asia',
    'China': 'East Asia', 'Japan': 'East Asia', 'South Korea': 'East Asia',
    'Taiwan': 'East Asia', 'Hong Kong': 'East Asia',
    'Egypt': 'MENA', 'Turkey': 'MENA', 'Iran': 'MENA', 'Morocco': 'MENA',
    'Algeria': 'MENA', 'Tunisia': 'MENA', 'Jordan': 'MENA', 'Lebanon': 'MENA',
    'Israel': 'MENA', 'Saudi Arabia': 'MENA', 'UAE': 'MENA',
    'Australia': 'Oceania', 'New Zealand': 'Oceania',
}

COUNTRY_FLAGS = {
    'United States': '🇺🇸', 'Canada': '🇨🇦', 'Mexico': '🇲🇽', 'Brazil': '🇧🇷',
    'Argentina': '🇦🇷', 'Chile': '🇨🇱', 'Colombia': '🇨🇴', 'Peru': '🇵🇪',
    'United Kingdom': '🇬🇧', 'Germany': '🇩🇪', 'France': '🇫🇷', 'Italy': '🇮🇹',
    'Spain': '🇪🇸', 'Netherlands': '🇳🇱', 'Sweden': '🇸🇪', 'Norway': '🇳🇴',
    'Denmark': '🇩🇰', 'Finland': '🇫🇮', 'Switzerland': '🇨🇭', 'Austria': '🇦🇹',
    'Belgium': '🇧🇪', 'Portugal': '🇵🇹', 'Poland': '🇵🇱', 'Greece': '🇬🇷',
    'South Africa': '🇿🇦', 'Nigeria': '🇳🇬', 'Kenya': '🇰🇪', 'Ghana': '🇬🇭',
    'Ethiopia': '🇪🇹', 'Tanzania': '🇹🇿', 'Senegal': '🇸🇳', 'Uganda': '🇺🇬',
    'India': '🇮🇳', 'Pakistan': '🇵🇰', 'Bangladesh': '🇧🇩', 'Indonesia': '🇮🇩',
    'Thailand': '🇹🇭', 'Vietnam': '🇻🇳', 'Philippines': '🇵🇭', 'Malaysia': '🇲🇾',
    'Sri Lanka': '🇱🇰',
    'China': '🇨🇳', 'Japan': '🇯🇵', 'South Korea': '🇰🇷', 'Taiwan': '🇹🇼',
    'Egypt': '🇪🇬', 'Turkey': '🇹🇷', 'Morocco': '🇲🇦', 'Tunisia': '🇹🇳',
    'Jordan': '🇯🇴', 'Lebanon': '🇱🇧', 'Israel': '🇮🇱',
    'Australia': '🇦🇺', 'New Zealand': '🇳🇿',
}

# ── HELPERS ────────────────────────────────────────────────────────────────────

def read_csv_dedup(path):
    """
    Like csv.DictReader but makes duplicate column names unique by appending
    _2, _3, ... so that repeated 'Select all that apply' headers are preserved.
    """
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.reader(f)
        raw_headers = next(reader)
        seen = {}
        headers = []
        for h in raw_headers:
            if h in seen:
                seen[h] += 1
                headers.append(f'{h}_{seen[h]}')
            else:
                seen[h] = 1
                headers.append(h)
        return [dict(zip(headers, row)) for row in reader]

def slugify(text):
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]', '-', text.lower())).strip('-')

def parse_list(text):
    """Split a free-text field into a list. Handles semicolons, commas, newlines."""
    if not text or not text.strip():
        return []
    items = re.split(r'\s*[;,\n]\s*', text)
    return [i.strip() for i in items if i.strip()]

# Known EPE topic strings (sorted longest-first for greedy matching)
_EPE_TOPICS_SORTED = sorted([
    'Care economy and social reproduction',
    'Climate, green transition, and energy policy',
    'Comparative capitalism and varieties of capitalism',
    'Corporate governance and ownership',
    'Development economics and state capacity',
    'Digital economy and platform labor',
    'Feminist political economy',
    'Financialization and financial markets',
    'Global value chains and trade',
    'Housing, land, and urban economy',
    'Industrial policy and structural transformation',
    'Inequality and redistribution',
    'Labor markets, unions, and employment',
    'Migration and labor mobility',
    'Monetary policy, central banking, and debt',
    'Post-colonial and decolonial political economy',
    'Racial capitalism and economic justice',
    'Social protection and welfare state',
    'State-market relations and regulation',
    'Technology, automation, and AI',
    'Other (please describe below)',
], key=len, reverse=True)

def parse_checkbox_topics(text):
    """
    Parse a Google Forms checkbox export where options are joined by ', '.
    Uses greedy known-vocabulary matching so multi-comma option names
    (e.g. 'Labor markets, unions, and employment') are kept intact.
    Falls back to comma-splitting for unrecognised tokens.
    """
    if not text or not text.strip():
        return []
    results = []
    remaining = text.strip()
    while remaining:
        matched = False
        for topic in _EPE_TOPICS_SORTED:
            if remaining == topic or remaining.startswith(topic + ', '):
                if topic.lower() != 'other (please describe below)':
                    results.append(topic)
                remaining = remaining[len(topic):].lstrip(', ')
                matched = True
                break
        if not matched:
            # Not a known topic — take up to the next ', ' as a free-text entry
            idx = remaining.find(', ')
            token = remaining[:idx].strip() if idx != -1 else remaining.strip()
            if token:
                results.append(token)
            remaining = remaining[idx + 2:] if idx != -1 else ''
    return results

def parse_timestamp(ts):
    for fmt in ['%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M', '%Y-%m-%d']:
        try:
            return datetime.strptime(ts.strip(), fmt)
        except ValueError:
            pass
    return datetime.min

def get(row, col_map, key):
    col = col_map.get(key, '')
    return row.get(col, '').strip()

# ── CENTERS ────────────────────────────────────────────────────────────────────

def merge_topics(row, col_map, checkbox_key, text_key):
    """Combine checkbox selections and free-text overflow into one list."""
    items = parse_checkbox_topics(get(row, col_map, checkbox_key))
    items += parse_list(get(row, col_map, text_key))
    return items

def process_centers(csv_path):
    if not csv_path.exists():
        print(f'  [SKIP] {csv_path} not found — keeping existing centers.json.')
        return None

    rows = read_csv_dedup(csv_path)
    print(f'  {len(rows)} center response(s) in CSV.')

    # Deduplicate by center name, keep latest timestamp
    by_name = {}
    for row in rows:
        name = row.get(CENTER_COLUMNS['name'], '').strip()
        if not name:
            continue
        ts = parse_timestamp(row.get(CENTER_COLUMNS['timestamp'], ''))
        if name not in by_name or ts > by_name[name][0]:
            by_name[name] = (ts, row)

    dupes = len(rows) - len(by_name)
    if dupes:
        print(f'  {dupes} duplicate submission(s) resolved (latest kept).')
    print(f'  {len(by_name)} unique center(s).')

    centers = []
    for name, (ts, row) in sorted(by_name.items()):
        country = get(row, CENTER_COLUMNS, 'country')
        centers.append({
            'id':                 slugify(name),
            'name':               name,
            'institution':        get(row, CENTER_COLUMNS, 'institution'),
            'city':               get(row, CENTER_COLUMNS, 'city'),
            'state':              get(row, CENTER_COLUMNS, 'state'),
            'country':            country,
            'region':             COUNTRY_TO_REGION.get(country, 'Other'),
            'flag':               COUNTRY_FLAGS.get(country, ''),
            'website':            get(row, CENTER_COLUMNS, 'website'),
            'logo_url':           get(row, CENTER_COLUMNS, 'logo_url'),
            'director':           get(row, CENTER_COLUMNS, 'director'),
            'contact':            get(row, CENTER_COLUMNS, 'contact'),
            'year_established':   get(row, CENTER_COLUMNS, 'year_established'),
            'topics_current':     merge_topics(row, CENTER_COLUMNS, 'topics_current', 'topics_current_text'),
            'topics_anticipated': merge_topics(row, CENTER_COLUMNS, 'topics_anticipated', 'topics_anticipated_text'),
            'topics_would_like':  merge_topics(row, CENTER_COLUMNS, 'topics_would_like', 'topics_would_like_text'),
            'focus_areas':        parse_list(get(row, CENTER_COLUMNS, 'focus_areas')),
            'current_projects':   get(row, CENTER_COLUMNS, 'current_projects'),
            'funding_sources':    get(row, CENTER_COLUMNS, 'funding_sources'),
            'problems':           get(row, CENTER_COLUMNS, 'problems'),
            'opportunities':      get(row, CENTER_COLUMNS, 'opportunities'),
            'connected_networks': parse_list(get(row, CENTER_COLUMNS, 'connected_networks')),
            'notes':              get(row, CENTER_COLUMNS, 'notes'),
            'updated':            ts.strftime('%Y-%m-%d') if ts != datetime.min else '',
        })
    return centers

# ── INDIVIDUALS ────────────────────────────────────────────────────────────────

def process_individuals(csv_path, centers):
    if not csv_path.exists():
        print(f'  [SKIP] {csv_path} not found — keeping existing individuals.json.')
        return None

    center_lookup = {c['name'].lower(): c['id'] for c in (centers or [])}

    rows = read_csv_dedup(csv_path)
    print(f'  {len(rows)} individual response(s) in CSV.')

    # Deduplicate by email (fallback to name)
    by_key = {}
    for row in rows:
        email = row.get(INDIVIDUAL_COLUMNS['email'], '').strip().lower()
        name  = row.get(INDIVIDUAL_COLUMNS['name'],  '').strip()
        key   = email or slugify(name)
        if not key:
            continue
        ts = parse_timestamp(row.get(INDIVIDUAL_COLUMNS['timestamp'], ''))
        if key not in by_key or ts > by_key[key][0]:
            by_key[key] = (ts, row)

    dupes = len(rows) - len(by_key)
    if dupes:
        print(f'  {dupes} duplicate submission(s) resolved (latest kept).')
    print(f'  {len(by_key)} unique individual(s).')

    individuals = []
    for key, (ts, row) in sorted(by_key.items()):
        name        = get(row, INDIVIDUAL_COLUMNS, 'name')
        center_name = get(row, INDIVIDUAL_COLUMNS, 'center_name')
        country     = get(row, INDIVIDUAL_COLUMNS, 'country')
        individuals.append({
            'id':                  slugify(name) if name else key,
            'name':                name,
            'title':               get(row, INDIVIDUAL_COLUMNS, 'title'),
            'center_id':           center_lookup.get(center_name.lower(), ''),
            'center_name':         center_name,
            'institution':         get(row, INDIVIDUAL_COLUMNS, 'institution'),
            'country':             country,
            'region':              COUNTRY_TO_REGION.get(country, 'Other'),
            'email':               get(row, INDIVIDUAL_COLUMNS, 'email'),
            'website':             get(row, INDIVIDUAL_COLUMNS, 'website'),
            'topics_current':      merge_topics(row, INDIVIDUAL_COLUMNS, 'topics_current', 'topics_current_text'),
            'topics_anticipated':  merge_topics(row, INDIVIDUAL_COLUMNS, 'topics_anticipated', 'topics_anticipated_text'),
            'topics_would_like':   merge_topics(row, INDIVIDUAL_COLUMNS, 'topics_would_like', 'topics_would_like_text'),
            'teaching_regions':    parse_list(get(row, INDIVIDUAL_COLUMNS, 'teaching_regions')),
            'teaching_levels':     parse_list(get(row, INDIVIDUAL_COLUMNS, 'teaching_levels')),
            'connected_networks':  parse_list(get(row, INDIVIDUAL_COLUMNS, 'connected_networks')),
            'problems':            get(row, INDIVIDUAL_COLUMNS, 'problems'),
            'opportunities':       get(row, INDIVIDUAL_COLUMNS, 'opportunities'),
            'notes':               get(row, INDIVIDUAL_COLUMNS, 'notes'),
            'updated':             ts.strftime('%Y-%m-%d') if ts != datetime.min else '',
        })
    return individuals

# ── CSV AUTO-DETECTION ─────────────────────────────────────────────────────────

def find_latest_csv(data_dir, keywords):
    """
    Search data/, csv/, and the project root for CSVs whose filename contains
    any keyword (case-insensitive). Returns the most recently modified match.
    """
    root = data_dir.parent
    search_dirs = [data_dir, root / 'csv', root]
    candidates = [
        p for d in search_dirs if d.exists()
        for p in d.glob('*.csv')
        if any(k.lower() in p.name.lower() for k in keywords)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    data_dir = Path(__file__).parent.parent / 'data'
    print('EPE Network — Data Synthesis')
    print('=' * 40)

    # Auto-detect latest CSVs by keyword match on filename, newest file wins.
    center_csv = (
        find_latest_csv(data_dir, ['center', 'centres'])
        or data_dir / 'centers_responses.csv'
    )
    individual_csv = (
        find_latest_csv(data_dir, ['scholar', 'individual', 'researcher'])
        or data_dir / 'individuals_responses.csv'
    )

    print(f'\nCenter CSV:     {center_csv.name}')
    print(f'Individual CSV: {individual_csv.name}')

    print('\nProcessing centers…')
    centers = process_centers(center_csv)
    if centers is not None:
        out = data_dir / 'centers.json'
        out.write_text(json.dumps(centers, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'  ✓ Wrote {out} ({len(centers)} centers)')
    else:
        centers_json = data_dir / 'centers.json'
        centers = json.loads(centers_json.read_text()) if centers_json.exists() else []

    print('\nProcessing individuals…')
    individuals = process_individuals(individual_csv, centers)
    if individuals is not None:
        out = data_dir / 'individuals.json'
        out.write_text(json.dumps(individuals, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'  ✓ Wrote {out} ({len(individuals)} individuals)')

    print('\nDone. Commit data/*.json to GitHub to publish changes.')

if __name__ == '__main__':
    main()
