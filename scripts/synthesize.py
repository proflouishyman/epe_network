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
    'topics_current':       'Current Research Topics',
    'topics_anticipated':   'Anticipated Research Topics',
    'topics_would_like':    'Topics You Would Like to Work On',
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
    'topics_current':      'Current Research Topics',
    'topics_anticipated':  'Anticipated Research Topics',
    'topics_would_like':   'Topics You Would Like to Work On',
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

def slugify(text):
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]', '-', text.lower())).strip('-')

def parse_list(text):
    """Split a free-text field into a list. Handles semicolons, commas, newlines."""
    if not text or not text.strip():
        return []
    items = re.split(r'\s*[;,\n]\s*', text)
    return [i.strip() for i in items if i.strip()]

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

def process_centers(csv_path):
    if not csv_path.exists():
        print(f'  [SKIP] {csv_path} not found — keeping existing centers.json.')
        return None

    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
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
            'topics_current':     parse_list(get(row, CENTER_COLUMNS, 'topics_current')),
            'topics_anticipated': parse_list(get(row, CENTER_COLUMNS, 'topics_anticipated')),
            'topics_would_like':  parse_list(get(row, CENTER_COLUMNS, 'topics_would_like')),
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

    with open(csv_path, newline='', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
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
            'topics_current':      parse_list(get(row, INDIVIDUAL_COLUMNS, 'topics_current')),
            'topics_anticipated':  parse_list(get(row, INDIVIDUAL_COLUMNS, 'topics_anticipated')),
            'topics_would_like':   parse_list(get(row, INDIVIDUAL_COLUMNS, 'topics_would_like')),
            'teaching_regions':    parse_list(get(row, INDIVIDUAL_COLUMNS, 'teaching_regions')),
            'teaching_levels':     parse_list(get(row, INDIVIDUAL_COLUMNS, 'teaching_levels')),
            'connected_networks':  parse_list(get(row, INDIVIDUAL_COLUMNS, 'connected_networks')),
            'problems':            get(row, INDIVIDUAL_COLUMNS, 'problems'),
            'opportunities':       get(row, INDIVIDUAL_COLUMNS, 'opportunities'),
            'notes':               get(row, INDIVIDUAL_COLUMNS, 'notes'),
            'updated':             ts.strftime('%Y-%m-%d') if ts != datetime.min else '',
        })
    return individuals

# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    data_dir = Path(__file__).parent.parent / 'data'
    print('EPE Network — Data Synthesis')
    print('=' * 40)

    print('\nProcessing centers…')
    centers = process_centers(data_dir / 'centers_responses.csv')
    if centers is not None:
        out = data_dir / 'centers.json'
        out.write_text(json.dumps(centers, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'  ✓ Wrote {out} ({len(centers)} centers)')
    else:
        centers_json = data_dir / 'centers.json'
        centers = json.loads(centers_json.read_text()) if centers_json.exists() else []

    print('\nProcessing individuals…')
    individuals = process_individuals(data_dir / 'individuals_responses.csv', centers)
    if individuals is not None:
        out = data_dir / 'individuals.json'
        out.write_text(json.dumps(individuals, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f'  ✓ Wrote {out} ({len(individuals)} individuals)')

    print('\nDone. Commit data/*.json to GitHub to publish changes.')

if __name__ == '__main__':
    main()
